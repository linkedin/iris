import datetime
import logging
import ujson
from falcon import HTTP_201, HTTPBadRequest, HTTPNotFound

from iris import db

logger = logging.getLogger(__name__)


class alertmanager(object):
    allow_read_no_auth = False

    def validate_post(self, body):
        if not all(k in body for k in("version", "status", "alerts")):
            raise HTTPBadRequest('missing version, status and/or alert attributes')

        if 'iris_plan' not in body["groupLabels"]:
            raise HTTPBadRequest('missing iris_plan in group labels')

    def create_context(self, body):
        context_json_str = ujson.dumps(body)
        if len(context_json_str) > 65535:
            logger.warning('POST to alertmanager exceeded acceptable size')
            raise HTTPBadRequest('Context too long')

        return context_json_str

    def on_post(self, req, resp):
        '''
        This endpoint is compatible with the webhook post from Alertmanager.
        Simply configure alertmanager with a receiver pointing to iris, like
        so:

        receivers:
        - name: 'iris-team1'
          webhook_configs:
            - url: http://iris:16649/v0/webhooks/alertmanager?application=test-app&key=sdffdssdf

        Where application points to an application and key in Iris.

        For every POST from alertmanager, a new incident will be created, if the iris_plan label
        is attached to an alert.
        '''
        alert_params = ujson.loads(req.context['body'])
        self.validate_post(alert_params)

        with db.guarded_session() as session:
            plan = alert_params['groupLabels']['iris_plan']
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
                logger.warning('no plan template exists for this app')
                raise HTTPBadRequest('No plan template actions exist for this app')

            data = {
                'plan_id': plan_id,
                'created': datetime.datetime.utcnow(),
                'application_id': app['id'],
                'context': context_json_str,
                'current_step': 0,
                'active': True,
            }

            incident_id = session.execute(
                '''INSERT INTO `incident` (`plan_id`, `created`, `context`,
                                           `current_step`, `active`, `application_id`)
                   VALUES (:plan_id, :created, :context, 0, :active, :application_id)''',
                data).lastrowid

            session.commit()
            session.close()

        resp.status = HTTP_201
        resp.set_header('Location', '/incidents/%s' % incident_id)
        resp.body = ujson.dumps(incident_id)
