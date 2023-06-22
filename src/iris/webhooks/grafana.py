import datetime
import time
import logging
import ujson
from falcon import HTTP_201, HTTPBadRequest, HTTPInvalidParam

from iris import db
from iris import utils
from iris.webhooks.webhook import webhook

logger = logging.getLogger(__name__)


class grafana(webhook):
    allow_read_no_auth = False

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
        incident_data = {
            'id': incident_id,
            'plan': plan,
            'plan_id': plan_id,
            'created': int(time.time()),
            'application': app.get("name"),
            'context': alert_params
        }
        self.custom_incident_handler(incident_data)
