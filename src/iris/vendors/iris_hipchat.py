# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import logging
import requests
import time
from iris.constants import HIPCHAT_SUPPORT

logger = logging.getLogger(__name__)


class iris_hipchat(object):
    supports = frozenset([HIPCHAT_SUPPORT])

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
        self.room_id = int(self.config.get('room_id'))
        self.debug = self.config.get('debug')
        self.endpoint_url = self.config.get('base_url')
        self.timeout = config.get('timeout', 10)

        self.headers = {
            'Content-type': 'application/json',
        }

    def get_message_payload(self, message, mention):
        """Send notification to specified HipChat room"""
        clean_message = "{0} {1}".format(mention, message['body'])
        message_dict = {
            'message': clean_message,
            'color': 'red',
            'notify': 'true',
            'message_format': "text",
        }
        return message_dict

    def parse_destination(self, destination):
        """Determine room_id, token and user to mention
           We accept 3 formats:
             - Just a mention (@testuser)
             - Room_id and Token (12341;a20asdfgjahdASDfaskw)
             - Room_id, Token and mention (12341;a20asdfgjahdASDfaskw;@testuser)
        """
        room_id = self.room_id
        token = self.token
        mention = ""

        if destination.startswith("@"):
            mention = destination
        elif ";" in destination:
            dparts = destination.split(";")
            if len(dparts) == 3:
                try:
                    room_id = int(dparts[0])
                except ValueError:
                    logger.error("Invalid destination: %s. Using default room_id", destination)
                token = dparts[1]
                mention = dparts[2]
            elif len(dparts) == 2:
                try:
                    room_id = int(dparts[0])
                except ValueError:
                    logger.error("Invalid destination: %s. Using default room_id", destination)
                token = dparts[1]
            else:
                logger.error("Invalid destination: %s. Contains %s fields.", destination, len(dparts))
        else:
            logger.error("Invalid destination: %s. Neither @user or ; separated value.", destination)

        return room_id, token, mention

    def send_message(self, message):
        start = time.time()
        room_id, token, mention = self.parse_destination(message['destination'])

        payload = self.get_message_payload(message, mention)
        notification_url = '{0}/v2/room/{1}/notification'.format(self.endpoint_url, room_id)
        params = {'auth_token': token}

        if self.debug:
            logger.info('debug: %s', payload)
        else:
            try:
                response = requests.post(notification_url,
                                         headers=self.headers,
                                         params=params,
                                         json=payload,
                                         proxies=self.proxy,
                                         timeout=self.timeout)
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
