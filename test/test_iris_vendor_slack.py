#!/usr/bin/env python
# -*- coding:utf-8 -*-

from iris.vendors.iris_slack import iris_slack
import ujson as json


def test_atttachments_construction_for_incident():
    slack_vendor = iris_slack({
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
        'body': 'test body',
        'message_id': 456,
        'destination': 'user1'
    }
    msg_payload = slack_vendor.get_message_payload(fake_msg)
    assert msg_payload['text'] == '[grafana] %s' % fake_msg['body']
    assert msg_payload['token'] == 'abc'
    assert msg_payload['channel'] == '@user1'

    attachments = msg_payload['attachments']
    assert json.loads(attachments) == [{
        'fallback': 'foo fallback',
        'pretext': 'foo pretext',
        'title': 'Iris incident %r' % fake_msg['incident_id'],
        'mrkdwn_in': ['pretext'],
        'attachment_type': 'default',
        'callback_id': fake_msg['message_id'],
        'color': 'danger',
        'title_link': 'http://foo.bar/incidents/%d' % fake_msg['incident_id'],
        'actions': [
            {
                'name': 'claim',
                'text': 'Claim Incident',
                'type': 'button',
                'value': 'claimed'
            },
            {
                'name': 'claim all',
                'text': 'Claim All',
                'style': 'danger',
                'type': 'button',
                'value': 'claimed all',
                "confirm": {
                    "title": "Are you sure?",
                    "text": "This will claim all active incidents targeting you.",
                    "ok_text": "Yes",
                    "dismiss_text": "No"
                }
            }
        ]
    }]


def test_atttachments_construction_for_notification():
    slack_vendor = iris_slack({
        'auth_token': 'abc',
        'iris_incident_url': 'http://foo.bar/incidents',
        'message_attachments': {
            'fallback': 'foo fallback',
            'pretext': 'foo pretext',
        }
    })
    fake_msg = {
        'application': 'grafana',
        'body': 'test body notification',
        'destination': 'user1'
    }
    msg_payload = slack_vendor.get_message_payload(fake_msg)
    assert msg_payload == {
        'text': '[grafana] %s' % fake_msg['body'],
        'token': 'abc',
        'channel': '@user1'
    }
