from __future__ import absolute_import

import datetime
import logging
import ujson
import time
from falcon import HTTP_201, HTTPBadRequest, HTTPNotFound

from iris import db
from iris import utils
from iris.custom_incident_handler import CustomIncidentHandlerDispatcher
from iris.constants import PRIORITY_PRECEDENCE_MAP

logger = logging.getLogger(__name__)


class webhook(object):
    allow_read_no_auth = False

    def __init__(self, config):
        self.custom_incident_handler_dispatcher = CustomIncidentHandlerDispatcher(config)
        # if True, we enable metavariables in the context everywhere, if False they will be enabled only for plans in allow list
        self.enable_default_metavariables_in_context = config.get('enable_default_metavariables_in_context', False)
        self.triage_allow_list = config.get('triage_allow_list', [])

    def validate_post(self, body):
        pass

    def create_context(self, body):
        context_json_str = ujson.dumps(body)
        if len(context_json_str) > 65535:
            logger.warn('POST exceeded acceptable size of 65535 characters')
            raise HTTPBadRequest('Context too long, must be < 65535 characters')

        return context_json_str

    def on_post(self, req, resp, plan):
        '''
        For every POST, a new incident will be created, if the plan label is
        attached to an alert. The iris application and key should be provided
        in the url params. The plan id can be taken from the post body or url
        params passed by the webhook subclass.
        '''
        alert_params = ujson.loads(req.context['body'])
        self.validate_post(alert_params)

        with db.guarded_session() as session:
            plan_id = session.execute('SELECT `plan_id` FROM `plan_active` WHERE `name` = :plan',
                                      {'plan': plan}).scalar()
            if not plan_id:
                raise HTTPNotFound()

            app = req.context['app']

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
                logger.warn('no plan template exists for this app')
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
            # adding additional context
            if self.enable_default_metavariables_in_context or plan in self.triage_allow_list:
                iris_metacontext = {'incident_id': incident_id, 'created': data.get('created')}
                data['iris'] = iris_metacontext

                context_json_str = self.create_context(data)
                session.execute('''UPDATE `incident` SET `context` = :context_json_str where `id` = :incident_id ''', {'context_json_str': context_json_str, 'incident_id': incident_id})

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

    def custom_incident_handler(self, incident_data):

        if not self.custom_incident_handler_dispatcher.handlers:
            return

        single_plan_query = '''SELECT `plan`.`id` as `id`, `plan`.`name` as `name`,
            `plan`.`threshold_window` as `threshold_window`, `plan`.`threshold_count` as `threshold_count`,
            `plan`.`aggregation_window` as `aggregation_window`, `plan`.`aggregation_reset` as `aggregation_reset`,
            `plan`.`description` as `description`, UNIX_TIMESTAMP(`plan`.`created`) as `created`,
            `target`.`name` as `creator`, IF(`plan_active`.`plan_id` IS NULL, FALSE, TRUE) as `active`,
            `plan`.`tracking_type` as `tracking_type`, `plan`.`tracking_key` as `tracking_key`,
            `plan`.`tracking_template` as `tracking_template`
        FROM `plan` JOIN `target` ON `plan`.`user_id` = `target`.`id`
        LEFT OUTER JOIN `plan_active` ON `plan`.`id` = `plan_active`.`plan_id`'''

        single_plan_query_steps = '''SELECT `plan_notification`.`id` as `id`,
            `plan_notification`.`step` as `step`,
            `plan_notification`.`repeat` as `repeat`,
            `plan_notification`.`wait` as `wait`,
            `plan_notification`.`optional` as `optional`,
            `target_role`.`name` as `role`,
            `target`.`name` as `target`,
            `plan_notification`.`template` as `template`,
            `priority`.`name` as `priority`,
            `plan_notification`.`dynamic_index` AS `dynamic_index`
        FROM `plan_notification`
        LEFT OUTER JOIN `target` ON `plan_notification`.`target_id` = `target`.`id`
        LEFT OUTER JOIN `target_role` ON `plan_notification`.`role_id` = `target_role`.`id`
        JOIN `priority` ON `plan_notification`.`priority_id` = `priority`.`id`
        WHERE `plan_notification`.`plan_id` = %s
        ORDER BY `plan_notification`.`step`'''
        connection = db.engine.raw_connection()
        cursor = connection.cursor(db.dict_cursor)

        # get plan info
        query = single_plan_query + 'WHERE `plan`.`id` = %s'
        cursor.execute(query, incident_data.get("plan_id"))
        plan_details = cursor.fetchone()

        # get plan steps info
        step = 0
        steps = []
        cursor.execute(single_plan_query_steps, incident_data.get("plan_id"))
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
