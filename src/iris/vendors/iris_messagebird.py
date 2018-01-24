# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import logging
import requests
import time
import json
from iris.constants import SMS_SUPPORT

logger = logging.getLogger(__name__)


class iris_messagebird(object):
    supports = frozenset([SMS_SUPPORT])

    def __init__(self, config):
        self.config = config
        self.modes = {
            'sms': self.send_message
        }

        self.debug = self.config.get('debug')

        self.proxy = None
        if 'proxy' in self.config:
            host = self.config['proxy']['host']
            port = self.config['proxy']['port']
            self.proxy = {'http': 'http://%s:%s' % (host, port),
                          'https': 'https://%s:%s' % (host, port)}

        self.endpoint_url = 'https://rest.messagebird.com/messages'

        self.access_key = self.config.get('access_key')
        self.headers = {
            'Accept': 'application/json',
            'Authorization': 'AccessKey ' + self.access_key,
            'User-Agent': 'Iris',
            'Content-Type': 'application/json'
        }

    def get_message_payload(self, message):
        """Format a proper message dict"""
        message_dict = {
            'body': message['body'],
            'originator': 'Iris',
            'recipients': message['destination']
        }
        return message_dict

    def send_message(self, message):
        start = time.time()
        payload = self.get_message_payload(message)

        if self.debug:
            logger.info('debug: %s', payload)
        else:
            try:
                response = requests.post(self.endpoint_url,
                                         headers=self.headers,
                                         json=payload,
                                         proxies=self.proxy)
                if response.status_code == 201:
                    return time.time() - start
                else:
                    logger.error('Failed to send message to messagebird: %d. Response: %s',
                                 response.status_code, response.content)
            except Exception as err:
                logger.exception('messagebird post request failed: %s', err)

    def send(self, message, customizations=None):
        return self.modes[message['mode']](message)
