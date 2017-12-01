#!/usr/bin/env python
# -*- coding:utf-8 -*-

from iris.vendors.iris_hipchat import iris_hipchat
import ujson as json


def test_message_construction_for_incident():
    hipchat_vendor = iris_hipchat({
        'auth_token': 'abc',
        'iris_incident_url': 'http://foo.bar/incidents',
        'message_attachments': {
            'fallback': 'foo fallback',
            'pretext': 'foo pretext',
        }
    })
    fake_msg = {
        'application': 'grafana',
        'incident_id': 123,
        'body': u'test body',
        'message_id': 456,
        'destination': 'user1'
    }
    msg_payload = hipchat_vendor.get_message_payload(fake_msg)
    assert msg_payload['message'] == '@user1 %s' % fake_msg['body']
