# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from iris.constants import SMS_SUPPORT, CALL_SUPPORT
from iris.plugins import find_plugin
from twilio.rest import TwilioRestClient
from twilio.rest.resources import Connection
from iris import db
from sqlalchemy.exc import IntegrityError
import time
import urllib
import logging

logger = logging.getLogger(__name__)


class iris_twilio(object):
    supports = frozenset([SMS_SUPPORT, CALL_SUPPORT])

    def __init__(self, config):
        self.config = config
        if 'proxy' in self.config:
            Connection.set_proxy_info(self.config['proxy']['host'],
                                      self.config['proxy']['port'],
                                      proxy_rdns=True)
        self.modes = {
            SMS_SUPPORT: self.send_sms,
            CALL_SUPPORT: self.send_call,
        }

    def get_twilio_client(self):
        return TwilioRestClient(self.config['account_sid'],
                                self.config['auth_token'])

    def generate_message_text(self, message):
        content = []

        for key in ('subject', 'body'):
            value = message.get(key)
            if not isinstance(value, basestring):
                continue
            value = value.strip()
            if value:
                content.append(value)

        return '. '.join(content)

    def initialize_twilio_message_status(self, sid, message_id):
        session = db.Session()
        try:
            session.execute('''INSERT INTO `twilio_delivery_status` (`twilio_sid`, `message_id`)
                               VALUES (:sid, :mid)''', {'sid': sid, 'mid': message_id})
            session.commit()
        except IntegrityError:
            logger.exception('Failed initializing twilio delivery status row. sid: %s, mid: %s', sid, message_id)
        session.close()

    def send_sms(self, message):
        client = self.get_twilio_client()

        sender = client.messages.create
        from_ = self.config['twilio_number']
        start = time.time()
        content = self.generate_message_text(message)
        status_callback_url = self.config['relay_base_url'] + '/api/v0/twilio/status'
        result = sender(to=message['destination'],
                        from_=from_,
                        body=content[:480],
                        status_callback=status_callback_url)

        send_time = time.time() - start

        try:
            sid = result.sid
        except Exception:
            logger.exception('Failed getting Message SID from Twilio')
            sid = None

        message_id = message.get('message_id')

        if sid and message_id:
            self.initialize_twilio_message_status(sid, message_id)
        else:
            logger.warning('Not initializing twilio SMS status row (mid: %s, sid: %s)', message_id, sid)

        return send_time

    def send_call(self, message):
        plugin = find_plugin(message['application'])
        if not plugin:
            raise ValueError('not supported source: %(application)s' % message)

        client = self.get_twilio_client()
        sender = client.calls.create
        from_ = self.config['twilio_number']
        status_callback_url = self.config['relay_base_url'] + '/api/v0/twilio/status'
        content = self.generate_message_text(message)

        payload = {
            'content': content[:480],
            'loop': 3,
            'source': message['application'],
        }

        # If message_id is None or 0, go through says as iris can't handle
        # phone call response without the id
        message_id = message.get('message_id')
        if message_id:
            payload['message_id'] = message_id
            payload['instruction'] = plugin.get_phone_menu_text()
            relay_cb_url = '%s/api/v0/twilio/calls/gather?%s' % (
                self.config['relay_base_url'], urllib.urlencode(payload)
            )
        else:
            relay_cb_url = '%s/api/v0/twilio/calls/say?%s' % (
                self.config['relay_base_url'], urllib.urlencode(payload)
            )

        start = time.time()

        result = sender(to=message['destination'],
                        from_=from_,
                        if_machine='Continue',
                        url=relay_cb_url,
                        status_callback=status_callback_url)

        send_time = time.time() - start

        try:
            sid = result.sid
        except Exception:
            logger.exception('Failed getting Message SID from Twilio')
            sid = None

        if sid and message_id:
            self.initialize_twilio_message_status(sid, message_id)
        else:
            logger.warning('Not initializing twilio call status row (mid: %s, sid: %s)', message_id, sid)

        return send_time

    def send(self, message, customizations=None):
        return self.modes[message['mode']](message)
