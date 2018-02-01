# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import logging
from iris.constants import EMAIL_SUPPORT, IM_SUPPORT, CALL_SUPPORT, SMS_SUPPORT, SLACK_SUPPORT
from iris import db
from pyfcm import FCMNotification

logger = logging.getLogger(__name__)


class iris_dummy(object):
    supports = frozenset([EMAIL_SUPPORT, IM_SUPPORT, CALL_SUPPORT, SMS_SUPPORT, SLACK_SUPPORT])

    def __init__(self, config):
        self.time_taken = 1
        self.api_key = config['api_key']
        self.notification = config['notification_title']

    def get_fcm_client(self):
        return FCMNotification(api_key=self.api_key)

    def send(self, message, customizations=None):
        if isinstance(customizations, dict):
            time_taken = customizations.get('time_taken', self.time_taken)
        else:
            time_taken = self.time_taken

        connection = db.engine.raw_connection()
        cursor = connection.cursor()
        # TODO: consider APNS as well as FCM. For now, since FCM supports both, use it.
        cursor.execute('''SELECT `registration_id`
                          FROM `device` WHERE `user_id` =
                          (SELECT `id` FROM `target` WHERE `name` = %s
                          AND `type_id` = (SELECT `id` FROM `target_type` WHERE `name` = 'user'))''',
                       message['target'])
        registration_ids = [row[0] for row in cursor]
        fcm_client = self.get_fcm_client()
        try:
            response = fcm_client.notify_multiple_devices(registration_ids=registration_ids,
                                                          message_title=self.notification,
                                                          message_body=message.get('subject',''))
            invalid_ids = []
            for idx, result in enumerate(response['results']):
                if result.get('error') == 'NotRegistered':
                    invalid_ids.append(registration_ids[idx])
            if invalid_ids:
                cursor.execute('''DELETE FROM `device` WHERE `registration_id` IN %s''', (invalid_ids,))
                connection.commit()
        except:
            logger.exception('FCM request failed for %s', message['target'])
        cursor.close()
        connection.close()
        return time_taken
