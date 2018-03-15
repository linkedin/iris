# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import logging
from pyfcm import FCMNotification
from iris import db

logger = logging.getLogger(__name__)


class fcm(object):
    def __init__(self, config):
        self.config = config
        self.api_key = self.config.get('api_key')
        self.notification = self.config.get('notification_title')
        self.proxy = None
        if 'proxy' in self.config:
            host = self.config['proxy']['host']
            port = self.config['proxy']['port']
            self.proxy = {'http': 'http://%s:%s' % (host, port),
                          'https': 'https://%s:%s' % (host, port)}
        self.client = FCMNotification(api_key=self.api_key, proxy_dict=self.proxy)

    def send_push(self, message):
        # Tracking message have no target, skip sending push notification
        if 'target' not in message:
            return
        connection = db.engine.raw_connection()
        cursor = connection.cursor()
        cursor.execute('''SELECT `registration_id`
                          FROM `device` WHERE `user_id` =
                          (SELECT `id` FROM `target` WHERE `name` = %s
                          AND `type_id` = (SELECT `id` FROM `target_type` WHERE `name` = 'user'))''',
                       message['target'])
        registration_ids = [row[0] for row in cursor]
        if registration_ids:
            try:
                data_message = {'incident_id': message.get('incident_id')}
                response = self.client.notify_multiple_devices(registration_ids=registration_ids,
                                                               message_title=self.notification,
                                                               message_body=message.get('subject', ''),
                                                               data_message=data_message)
                invalid_ids = []
                for idx, result in enumerate(response['results']):
                    if result.get('error') == 'NotRegistered':
                        invalid_ids.append(registration_ids[idx])
                # Clean invalidated push notification IDs
                if invalid_ids:
                    cursor.execute('''DELETE FROM `device` WHERE `registration_id` IN %s''', (invalid_ids,))
                    connection.commit()
            except Exception:
                logger.exception('FCM request failed for message id %s', message.get('message_id'))
        cursor.close()
        connection.close()
