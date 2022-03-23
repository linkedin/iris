import datetime
import logging
import ujson
import json
import re
from falcon import HTTP_201, HTTPBadRequest, HTTPInvalidParam

from iris import db

logger = logging.getLogger(__name__)


class freshping(object):
    allow_read_no_auth = False

    def validate_post(self, body):
        if not all(k in body for k in ("title", "description", "tags", "ticket_id")):
            logger.warn('missing channel name attributes')
            raise HTTPBadRequest('missing channel name attributes')

    def unhtml(self, string):
        done = False
        while not done:
            temp = re.sub(r'<([^/]\S*)[^>]*>[\s\S]*?</\1>', '', string)
            done = temp == string
            string = temp
    # replace remaining standalone tags, if any
        string = re.sub(r'<[^>]*>', '', string)
        string = re.sub(r'\s{2,}', ' ', string)
        return string.strip()

    def cleanup(self, element):
        if isinstance(element, list):
            for i, item in enumerate(element):
                element[i] = self.cleanup(item)
        elif isinstance(element, dict):
            for key in element.keys():
                element[key] = self.cleanup(element[key])
        elif isinstance(element, str):
            element = self.unhtml(element)

        return element

    def create_context(self, body):
        context_json_str = ujson.dumps(body)
        data = json.loads(context_json_str)
        self.cleanup(data)
        json_string = json.dumps(data)
        print(json_string)
        if len(context_json_str) > 65535:
            logger.warn('POST to FreshPing exceeded acceptable size')
            raise HTTPBadRequest('Context too long')

        return context_json_str

    def on_post(self, req, resp):
        alert_params = ujson.loads(req.context['body'])
        self.validate_post(alert_params)

        with db.guarded_session() as session:
            plan = req.get_param('plan', True)
            plan_id = session.execute('SELECT `plan_id` FROM `plan_active` WHERE `name` = :plan',
                                      {'plan': plan}).scalar()
            if not plan_id:
                logger.warn('No active plan "%s" found', plan)
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
                logger.warn('no plan template exists for this app')
                raise HTTPBadRequest('No plan template actions exist for this app')

            data = {
                'plan_id': plan_id,
                'created': datetime.datetime.utcnow(),
                'application_id': app['id'],
                'context': context_json_str,
                'current_step': 0,
                'active': True,
            }

            session.execute(
                '''INSERT INTO `incident` (`plan_id`, `created`, `context`,
                                           `current_step`, `active`, `application_id`)
                   VALUES (:plan_id, :created, :context, 0, :active, :application_id)''',
                data).lastrowid

            session.commit()
            session.close()

        resp.status = HTTP_201
