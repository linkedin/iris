# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import ujson
import logging
import requests
import random
import time
from gevent import sleep
from iris.constants import SLACK_SUPPORT
from iris.custom_import import import_custom_module

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
        self.timeout = config.get('timeout', 10)
        self.sleep_range = config.get('sleep_range', 4)
        self.message_attachments = self.config.get('message_attachments', {})
        push_config = config.get('push_notification', {})
        self.push_active = push_config.get('activated', False)
        if self.push_active:
            self.notifier = import_custom_module('iris.push', push_config['type'])(push_config)

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
            # Display application if exists, otherwise it's an incident tracking message
            'text': '[%s] %s' % (message.get('application', 'Iris incident'),
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
        if not (destination.startswith('@') or destination.startswith('#')):
            destination = '@%s' % (destination)
        return destination

    def send_message(self, message):
        start = time.time()
        if self.push_active:
            self.notifier.send_push(message)
        payload = self.get_message_payload(message)
        try:
            response = requests.post(self.config['base_url'],
                                     data=payload,
                                     proxies=self.proxy,
                                     timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                if data['ok']:
                    return time.time() - start
                elif data.get('error') == 'channel_not_found':
                    logger.warning('Slack returned channel_not_found for destination %s', message.get('destination'))
                    return time.time() - start
                # If message is invalid:
                #   {u'ok': False, u'error': u'invalid_arg_name'}
                logger.error('Received an error from slack api: %s',
                             data['error'])
            elif response.status_code == 429:
                # Slack rate limiting. Sleep for a few seconds (chosen randomly to spread load),
                # then raise error to retry
                sleep_time = random.randrange(1, self.sleep_range)
                logger.warning('Hit slack rate limiting, sleeping for %s', sleep_time)
                sleep(sleep_time)
                response.raise_for_status()
            else:
                logger.error('Failed to send message to slack: %d',
                             response.status_code)
        except Exception:
            logger.exception('Slack post request failed')
            raise

    def send(self, message, customizations=None):
        return self.modes[message['mode']](message)
