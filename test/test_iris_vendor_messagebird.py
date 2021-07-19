#!/usr/bin/env python
# -*- coding:utf-8 -*-

from iris.vendors.iris_messagebird import iris_messagebird


def test_message_construction_for_incident():
    messagebird_vendor = iris_messagebird({
        'access_key': 'abc',
    })
    fake_msg = {
        'application': 'grafana',
        'incident_id': 123,
        'body': 'test body',
        'message_id': 456,
        'destination': '0612342341'
    }
    fake_msg['mode'] = 'call'
    msg_payload = messagebird_vendor.get_message_payload(fake_msg)

    assert msg_payload['originator'] == 'Iris'
    assert msg_payload['recipients'] == '%s' % fake_msg['destination']
    assert msg_payload['body'] == '%s' % fake_msg['body']
    assert 'repeat' in msg_payload

    fake_msg['mode'] = 'sms'
    msg_payload = messagebird_vendor.get_message_payload(fake_msg)
    assert 'repeat' not in msg_payload
