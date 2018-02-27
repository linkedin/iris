# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import logging
from iris.constants import EMAIL_SUPPORT, IM_SUPPORT, CALL_SUPPORT, SMS_SUPPORT, SLACK_SUPPORT

logger = logging.getLogger(__name__)


class iris_dummy(object):
    supports = frozenset([EMAIL_SUPPORT, IM_SUPPORT, CALL_SUPPORT, SMS_SUPPORT, SLACK_SUPPORT])

    def __init__(self, config):
        self.time_taken = 1

    def send(self, message, customizations=None):
        if isinstance(customizations, dict):
            time_taken = customizations.get('time_taken', self.time_taken)
        else:
            time_taken = self.time_taken
        if 'email_subject' in message:
            logger.info('SEND: %(destination)s %(email_subject)s', message)
        else:
            message['application'] = message.get('application')
            message['subject'] = message.get('subject', 'Tracking message')
            logger.info('SEND: %(mode)s %(application)s %(destination)s %(subject).25s', message)
        return time_taken
