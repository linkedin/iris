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
        # TODO: Verify title, title_link and text.
        att_json = {
            'fallback': self.message_attachments.get('fallback'),
            'pretext': self.message_attachments.get('pretext'),
            'title': 'Iris incident %r' % message['incident_id'],
            'mrkdwn_in': ['pretext'],
            'attachment_type': 'default',
            'callback_id': message.get('message_id'),
            'color': 'danger',
            'title_link': '%s/%s' % (
                self.config['iris_incident_url'], message['incident_id']),
            'actions': [
                {
                    'name': 'claim',
                    'text': 'Claim Incident',
                    'type': 'button',
                    'value': 'claimed'
                },
                {
                    'name': 'claim all',
                    'text': 'Claim All',
                    'style': 'danger',
                    'type': 'button',
                    'value': 'claimed all',
                    "confirm": {
                        "title": "Are you sure?",
                        "text": "This will claim all active incidents targeting you.",
                        "ok_text": "Yes",
                        "dismiss_text": "No"
                    }
                }
            ]
        }
        return ujson.dumps([att_json])

    def get_message_payload(self, message):
        slack_message = {
            'text': '[%s] %s' % (message.get('application', 'unknown app'),
                                 message['body']),
            'token': self.config['auth_token'],
            'channel': self.get_destination(message['destination'])
        }
        # only add interactive button for incidents
        if 'incident_id' in message:
            slack_message['attachments'] = self.construct_attachments(message)
        return slack_message

    def get_destination(self, destination):
        # If the destination doesn't have '@' this adds it
        if not destination.startswith('@'):
            destination = '@%s' % (destination)
        return destination

    def send_message(self, message):
        start = time.time()
        payload = self.get_message_payload(message)
        try:
            response = requests.post(self.config['base_url'],
                                     data=payload,
                                     proxies=self.proxy)
            if response.status_code == 200:
                data = response.json()
                if data['ok']:
                    return time.time() - start
                # If message is invalid:
                #   {u'ok': False, u'error': u'invalid_arg_name'}
                logger.error('Received an error from slack api: %s',
                             data['error'])
            else:
                logger.error('Failed to send message to slack: %d',
                             response.status_code)
        except Exception:
            logger.exception('Slack post request failed')

    def send(self, message, customizations=None):
        return self.modes[message['mode']](message)
