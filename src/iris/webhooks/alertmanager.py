from __future__ import absolute_import

import time
import hmac
import hashlib
import base64
import re
import os
import datetime
import logging
from urlparse import parse_qs
import ujson
from falcon import HTTP_200, HTTP_201, HTTP_204, HTTPBadRequest, HTTPNotFound, HTTPUnauthorized, HTTPForbidden, HTTPFound, HTTPInternalServerError, API
from sqlalchemy.exc import IntegrityError

from collections import defaultdict

from iris import db

logger = logging.getLogger(__name__)

class alertmanager(object):
    allow_read_no_auth = False

    def on_get(self, req, resp):
        raise HTTPNotFound()

    def on_post(self, req, resp):
        '''
        This endpoint is compatible with the webhook post from Alertmanager.
        Simply configure alertmanager with a receiver pointing to iris, like
        so:

        receivers:
        - name: 'iris-team1'
          webhook_configs:
            - url: http://iris:16649/v0/webhooks/alertmanager?application=test-app&key=sdffdssdf

        Where application points to an application and key it's key, in Iris.

        For every POST from alertmanager, a new incident will be created.
        '''
        logger.info("alertmanager hit!")
        alert_params = ujson.loads(req.context['body'])
        if not all (k in alert_params for k in ("version", "status", "alerts")):
            raise HTTPBadRequest('missing version, status and/or alert attributes')

        with db.guarded_session() as session:
            plan = req.context['plan']
            plan_id = session.execute('SELECT `plan_id` FROM `plan_active` WHERE `name` = :plan',
                                      {'plan': plan}).scalar()
            if not plan_id:
                raise HTTPNotFound()

            app = req.context['app']

            # create new context
            context = {}
            str_fields = ['status', 'groupKey', 'version', 'receiver', 'externalURL']

            for field in str_fields:
                context[field] = alert_params[field]

            cnt = 0
            for alert in alert_params['alerts']:
                cnt = cnt + 1
                field_prefix = "alert_" + str(cnt) + "_"
                context[field_prefix + "status"] = alert['status']
                context[field_prefix + "endsAt"] = alert['endsAt']
                context[field_prefix + "generatorURL"] = alert['generatorURL']
                context[field_prefix + "startsAt"] = alert['startsAt']

                labels = "; ".join([k + ": " + v for k, v in alert['labels'].items()])
                context[field_prefix + "labels"] = labels

                annotations = "; ".join([k + ": " + v for k, v in alert['annotations'].items()])
                context[field_prefix + "annotations"] = annotations

            for k, val in alert_params['groupLabels'].iteritems():
                context['groupLabel_' + k] = val

            for k, val in alert_params['commonLabels'].iteritems():
                context['commonLabels_' + k] = val

            for k, val in alert_params['commonAnnotations'].iteritems():
                context['commonAnnotations_' + k] = val

            context_json_str = ujson.dumps(context)
            if len(context_json_str) > 65535:
                logger.warn('POST to alertmanager exceeded acceptable size')
                raise HTTPBadRequest('Context too long')

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

            # if status is resolved, insert into the incident database
            # with a dynamic target and a plan that only ever sends out
            # 1 notification. This allows us to do 'resolved' notifications
            # without escalation
            if alert['status'] == "resolved":
                logger.info("got resolved incident")
                # lookup plan role and target
                # then insert incident with special resolved plan
                incident_id = session.execute(
                    '''INSERT INTO `incident` (`plan_id`, `created`, `context`,
                                               `current_step`, `active`, `application_id`)
                       VALUES (:plan_id, :created, :context, 0, :active, :application_id)''',
                    data).lastrowid
            else:
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
