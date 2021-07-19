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
        # FCM guarantees best-effort delivery with TTL 0
        self.ttl = self.config.get('ttl', 0)
        self.timeout = self.config.get('timeout', 10)
        self.default_notification = self.config.get('notification_title')
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
        cursor.execute('''SELECT `registration_id`, `platform`
                          FROM `device` WHERE `user_id` =
                          (SELECT `id` FROM `target` WHERE `name` = %s
                          AND `type_id` = (SELECT `id` FROM `target_type` WHERE `name` = 'user'))''',
                       message['target'])
        registration_ids = cursor.fetchall()
        android_ids = [row[0] for row in registration_ids if row[1] == 'Android']
        ios_ids = [row[0] for row in registration_ids if row[1] == 'iOS']
        invalid_ids = []
        failed_ids = []
        # Handle iOS and Android ids separately. Mobile app requires different formats for
        # correct behavior on both platforms (esp with respect to action buttons)
        if ios_ids:
            try:
                data_message = {'incident_id': message.get('incident_id')}
                response = self.client.notify_multiple_devices(
                    registration_ids=ios_ids,
                    message_title=message.get('subject', self.default_notification),
                    message_body=message.get('body', ''),
                    sound='default',
                    time_to_live=self.ttl,
                    data_message=data_message,
                    timeout=self.timeout,
                    click_action='incident'
                )
                for idx, result in enumerate(response['results']):
                    error = result.get('error')
                    if error == 'NotRegistered':
                        invalid_ids.append(ios_ids[idx])
                    elif error is not None:
                        failed_ids.append((ios_ids[idx], error))
            except Exception:
                logger.exception('FCM request failed for message id %s', message.get('message_id'))
        if android_ids:
            try:
                data_message = {'incident_id': message.get('incident_id'),
                                'title': message.get('subject', self.default_notification),
                                'message': message.get('body', ''),
                                'actions': [{
                                    'title': 'Claim',
                                    'callback': 'claimIncident',
                                    'foreground': True
                                }]
                                }
                response = self.client.multiple_devices_data_message(
                    registration_ids=android_ids,
                    time_to_live=self.ttl,
                    data_message=data_message,
                    timeout=self.timeout
                )
                for idx, result in enumerate(response['results']):
                    error = result.get('error')
                    if error == 'NotRegistered':
                        invalid_ids.append(android_ids[idx])
                    elif error is not None:
                        failed_ids.append((android_ids[idx], error))
            except Exception:
                logger.exception('FCM request failed for message id %s', message.get('message_id'))
        # Clean invalidated push notification IDs
        if invalid_ids:
            cursor.execute('''DELETE FROM `device` WHERE `registration_id` IN %s''', (invalid_ids,))
            connection.commit()
        if failed_ids:
            logger.exception('FCM requests failed: %s', failed_ids)
        cursor.close()
        connection.close()
