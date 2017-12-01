# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import logging
import requests
import time
from iris.constants import IM_SUPPORT

logger = logging.getLogger(__name__)


class iris_hipchat(object):
    supports = frozenset(['hipchat'])

    def __init__(self, config):
        self.config = config
        self.modes = {
            'hipchat': self.send_message
        }
        self.proxy = None
        if 'proxy' in self.config:
            host = self.config['proxy']['host']
            port = self.config['proxy']['port']
            self.proxy = {'http': 'http://%s:%s' % (host, port),
                          'https': 'https://%s:%s' % (host, port)}
        self.token = self.config.get('auth_token')
        self.room_id = self.config.get('room_id')
        self.debug = self.config.get('debug')
        self.endpoint_url = self.config.get('base_url')

        self.params = {'auth_token': self.token}
        self.notification_url = '{0}/v2/room/{1}/notification'.format(self.endpoint_url, self.room_id)
        self.headers = {
            'Content-type': 'application/json',
        }

    def get_message_payload(self, message):
        """Send notification to specified HipChat room"""
        clean_message = "@{0} {1}".format(message['destination'], message['body'])
        message_dict = {
            'message': clean_message,
            'color': 'red',
            'notify': 'true',
            'message_format': "text",
        }
        return message_dict

    def send_message(self, message):
        start = time.time()
        payload = self.get_message_payload(message)
        if self.debug:
            logger.info('debug: %s', self.message_dict)
        else:
            try:
                response = requests.post(self.notification_url,
                                         headers=self.headers,
                                         params=self.params,
                                         json=payload,
                                         proxies=self.proxy)
                if response.status_code == 200 or response.status_code == 204:
                    return time.time() - start
                else:
                    logger.error('Failed to send message to hipchat: %d',
                                 response.status_code)
                    logger.error("Response: %s", response.content)
            except Exception as err:
                logger.exception('Hipchat post request failed: %s', err)

    def send(self, message, customizations=None):
        return self.modes[message['mode']](message)
