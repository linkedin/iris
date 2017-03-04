# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from iris_api.constants import SMS_SUPPORT, CALL_SUPPORT
from iris_api.plugins import find_plugin
from twilio.rest import TwilioRestClient
from twilio.rest.resources import Connection
import time
import urllib


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

    def send_sms(self, message):
        client = self.get_twilio_client()

        sender = client.messages.create
        from_ = self.config['twilio_number']
        start = time.time()
        content = self.generate_message_text(message)
        sender(to=message['destination'],
               from_=from_,
               body=content[:480])

        return time.time() - start

    def send_call(self, message):
        plugin = find_plugin(message['application'])
        if not plugin:
            raise ValueError('not supported source: %(application)s' % message)

        client = self.get_twilio_client()
        sender = client.calls.create
        from_ = self.config['twilio_number']
        url = self.config['relay_base_url'] + '/api/v0/twilio/calls/gather?'
        content = self.generate_message_text(message)

        start = time.time()
        qs = urllib.urlencode({
            'content': content[:480],
            'instruction': plugin.get_phone_menu_text(),
            'loop': 3,
            'source': message['application'],
            'message_id': message.get('message_id', 0),
        })

        sender(to=message['destination'],
               from_=from_,
               if_machine='Continue',
               url=url + qs)

        return time.time() - start

    def send(self, message):
        return self.modes[message['mode']](message)
