#!/usr/bin/env python
# -*- coding:utf-8 -*-

from iris.vendors.iris_slack import iris_slack
import ujson as json


def test_atttachments_construction_for_incident():
    slack_vendor = iris_slack({
        'iris_incident_url': 'http://foo.bar/incidents',
        'message_attachments': {
            'fallback': 'foo fallback',
            'pretext': 'foo pretext',
        }
    })
    fake_msg = {
        'incident_id': 123,
        'subject': u'test subject',
        'body': u'test body',
        'message_id': 456,
    }
    attachments = slack_vendor.construct_attachments(fake_msg)
    assert json.loads(attachments) == [{
        'fallback': 'foo fallback',
        'pretext': 'foo pretext',
        'title': fake_msg['subject'],
        'text': fake_msg['body'],
        'mrkdwn_in': ['pretext'],
        'attachment_type': 'default',
        'callback_id': fake_msg['message_id'],
        'color': 'danger',
        'title_link': 'http://foo.bar/incidents/%d' % fake_msg['incident_id'],
        'actions': [{
            'name': 'claim',
            'text': 'Claim Incident',
            'type': 'button',
            'value': 'claimed',
        }]
    }]


def test_atttachments_construction_for_notification():
    slack_vendor = iris_slack({
        'iris_incident_url': 'http://foo.bar/incidents',
        'message_attachments': {
            'fallback': 'foo fallback',
            'pretext': 'foo pretext',
        }
    })
    fake_msg = {
        'subject': 'test subject',
        'body': 'test body',
    }
    attachments = slack_vendor.construct_attachments(fake_msg)
    assert json.loads(attachments) == [{
        'fallback': 'foo fallback',
        'pretext': 'foo pretext',
        'title': fake_msg['subject'],
        'text': fake_msg['body'],
        'mrkdwn_in': ['pretext'],
    }]
