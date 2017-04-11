# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import ujson
import logging
import requests
import time
from iris.constants import SLACK_SUPPORT

logger = logging.getLogger(__name__)


class iris_slack(object):
    supports = frozenset([SLACK_SUPPORT])

    def __init__(self, config):
        self.config = config
        # For now slack has only IM mode but we can expand it to send msg to a
        # channel  instead of a user
        self.modes = {
            SLACK_SUPPORT: self.send_message
        }
        self.proxy = None
        if 'proxy' in self.config:
            host = self.config['proxy']['host']
            port = self.config['proxy']['port']
            self.proxy = {'http': 'http://%s:%s' % (host, port),
                          'https': 'https://%s:%s' % (host, port)}
        self.message_attachments = self.config.get('message_attachments', {})

    def construct_attachments(self, message):
        # TODO:
        # 1. Verify title, title_link and text.
        # 2. Include message buttons. Need to update relay code.
        att_json = {
            'fallback': self.message_attachments.get('fallback'),
            'pretext': self.message_attachments.get('pretext'),
            'title': message['subject'],
            'text': message['body'],
            'mrkdwn_in': ['pretext'],
        }
        # only add interactive button for incidents
        if 'incident_id' in message:
            att_json['attachment_type'] = 'default'
            att_json['callback_id'] = message.get('message_id')
            att_json['color'] = 'danger'
            att_json['title_link'] = '%s/%s' % (
                self.config['iris_incident_url'], message['incident_id'])
            att_json['actions'] = [{
                'name': 'claim',
                'text': 'Claim Incident',
                'type': 'button',
                'value': 'claimed'
            }]
        return ujson.dumps([att_json])

    def get_destination(self, destination):
        # If the destination doesn't have '@' this adds it
        if not destination.startswith('@'):
            destination = '@%s' % (destination)
        return destination

    def send_message(self, message):
        start = time.time()
        slack_message = {
            'token': self.config['auth_token'],
            'channel': self.get_destination(message['destination']),
            'attachments': self.construct_attachments(message)
        }
        try:
            response = requests.post(self.config['base_url'],
                                     params=slack_message,
                                     headers={'Content-Type': 'application/json'},
                                     proxies=self.proxy)
            if response.status_code == 200:
                data = response.json()
                if data['ok']:
                    return time.time() - start
                # If message is invalid - {u'ok': False, u'error': u'invalid_arg_name'}
                logger.error('Received an error from slack api: %s', data['error'])
            else:
                logger.error('Failed to send message to slack:%d', response.status_code)
        except Exception:
            logger.exception('Slack post request failed')

    def send(self, message):
        return self.modes[message['mode']](message)
