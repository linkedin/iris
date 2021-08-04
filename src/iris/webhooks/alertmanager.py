from __future__ import absolute_import

import ujson
from falcon import HTTPBadRequest

from iris.webhooks.webhook import webhook


class alertmanager(webhook):

    def validate_post(self, body):
        if not all(k in body for k in("version", "status", "alerts")):
            raise HTTPBadRequest('missing version, status and/or alert attributes')

        if 'iris_plan' not in body["groupLabels"]:
            raise HTTPBadRequest('missing iris_plan in group labels')

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
        plan = alert_params['groupLabels']['iris_plan']
        super().on_post(req, resp, plan)
