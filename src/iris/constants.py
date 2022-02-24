# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

# Headers
XFRAME = ('X-Frame-Options', 'SAMEORIGIN')
XCONTENTTYPEOPTIONS = ('X-Content-Type-Options', 'nosniff')
XXSSPROTECTION = ('X-XSS-Protection', '1; mode=block')

# Avoid using magic strings when referring to the transports vendors support
SMS_SUPPORT = 'sms'
CALL_SUPPORT = 'call'
EMAIL_SUPPORT = 'email'
IM_SUPPORT = 'im'
SLACK_SUPPORT = 'slack'
HIPCHAT_SUPPORT = 'hipchat'

# Priorities listed in order of severity, ascending
PRIORITY_PRECEDENCE = ('low', 'medium', 'high', 'urgent')
PRIORITY_PRECEDENCE_MAP = {name: index for index, name in enumerate(PRIORITY_PRECEDENCE)}
