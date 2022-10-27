import datetime
import time
import logging
import ujson
from falcon import HTTP_201, HTTPBadRequest, HTTPInvalidParam

from iris import db
from iris import utils
from iris.custom_incident_handler import CustomIncidentHandlerDispatcher
from iris.constants import (PRIORITY_PRECEDENCE_MAP)
from .webhook_constants import (SINGLE_PLAN_QUERY_STEPS, SINGLE_PLAN_QUERY)

logger = logging.getLogger(__name__)


class grafana(object):
    allow_read_no_auth = False

    def __init__(self, config):
        self.custom_incident_handler_dispatcher = CustomIncidentHandlerDispatcher(config)

    def validate_post(self, body):
        if not all(k in body for k in ("ruleName", "state")):
            logger.warning('missing ruleName and/or state attributes')
            raise HTTPBadRequest('missing ruleName and/of state attributes')

    def create_context(self, body):
        context_json_str = ujson.dumps(body)
        if len(context_json_str) > 65535:
            logger.warning('POST to grafana exceeded acceptable size')
            raise HTTPBadRequest('Context too long')

        return context_json_str

    def on_post(self, req, resp):
        '''
        This endpoint is compatible with the webhook post from Grafana.
        Simply configure Grafana with a new notification channel with type 'webhook'
        and a plan parameter pointing to your iris plan.

        Name: 'iris-team1'
        Url: http://iris:16649/v0/webhooks/grafana?application=test-app&key=sdffdssdf&plan=team1
        '''
        alert_params = ujson.loads(req.context['body'])
        self.validate_post(alert_params)

        with db.guarded_session() as session:
            plan = req.get_param('plan', True)
            plan_id = session.execute('SELECT `plan_id` FROM `plan_active` WHERE `name` = :plan',
                                      {'plan': plan}).scalar()
            if not plan_id:
                logger.warning('No active plan "%s" found', plan)
                raise HTTPInvalidParam('plan does not exist or is not active')

            app = req.context['app']

            if not session.execute('SELECT EXISTS(SELECT 1 FROM `application` WHERE id = :id)', {'id': app['id']}).scalar():
                raise HTTPBadRequest('Invalid application')

            context_json_str = self.create_context(alert_params)

            app_template_count = session.execute('''
                SELECT EXISTS (
                  SELECT 1 FROM
                  `plan_notification`
                  JOIN `template` ON `template`.`name` = `plan_notification`.`template`
                  JOIN `template_content` ON `template_content`.`template_id` = `template`.`id`
                  WHERE `plan_notification`.`plan_id` = :plan_id
                  AND `template_content`.`application_id` = :app_id
                )
            ''', {'app_id': app['id'], 'plan_id': plan_id}).scalar()

            if not app_template_count:
                logger.warning('no plan template exists for this app')
                raise HTTPBadRequest('No plan template actions exist for this app')

            data = {
                'plan_id': plan_id,
                'created': datetime.datetime.utcnow(),
                'application_id': app['id'],
                'context': context_json_str,
                'current_step': 0,
                'active': True,
                'bucket_id': utils.generate_bucket_id()
            }

            incident_id = session.execute(
                '''INSERT INTO `incident` (`plan_id`, `created`, `context`,
                                           `current_step`, `active`, `application_id`, `bucket_id`)
                   VALUES (:plan_id, :created, :context, 0, :active, :application_id, :bucket_id)''',
                data).lastrowid

            session.commit()
            session.close()

        resp.status = HTTP_201
        resp.set_header('Location', '/incidents/%s' % incident_id)
        resp.body = ujson.dumps(incident_id)

        # optional incident handler to do additional tasks after the incident has been created
        if self.custom_incident_handler_dispatcher.handlers:
            incident_data = {
                'id': incident_id,
                'plan': plan,
                'created': int(time.time()),
                'application': app,
                'context': alert_params
            }
            connection = db.engine.raw_connection()
            cursor = connection.cursor(db.dict_cursor)

            # get plan info
            query = SINGLE_PLAN_QUERY + 'WHERE `plan`.`id` = %s'
            cursor.execute(query, plan_id)
            plan_details = cursor.fetchone()

            # get plan steps info
            step = 0
            steps = []
            cursor.execute(SINGLE_PLAN_QUERY_STEPS, plan_id)
            highest_seen_priority_rank = -1
            incident_data['priority'] = ''
            for notification in cursor:
                s = notification['step']
                if s != step:
                    l = [notification]
                    steps.append(l)
                    step = s
                else:
                    l.append(notification)

                # calculate priority for this incident based on the most severe priority
                # across all notifications within the plan
                priority_name = notification['priority']
                priority_rank = PRIORITY_PRECEDENCE_MAP.get(priority_name)
                if priority_rank is not None and priority_rank > highest_seen_priority_rank:
                    highest_seen_priority_rank = priority_rank
                    incident_data['priority'] = priority_name

            plan_details['steps'] = steps
            connection.close()
            incident_data["plan_details"] = plan_details
            self.custom_incident_handler_dispatcher.process_create(incident_data)
