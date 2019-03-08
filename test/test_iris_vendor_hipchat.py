#!/usr/bin/env python
# -*- coding:utf-8 -*-

from iris.vendors.iris_hipchat import iris_hipchat


def test_message_construction_for_incident():
    hipchat_vendor = iris_hipchat({
        'auth_token': 'abc',
        'iris_incident_url': 'http://foo.bar/incidents',
        'room_id': 1234,
    })
    fake_msg = {
        'application': 'grafana',
        'incident_id': 123,
        'body': 'test body',
        'message_id': 456,
        'destination': '@user1',
    }
    msg_payload = hipchat_vendor.get_message_payload(fake_msg, "@user1")
    assert msg_payload['message'] == '@user1 %s' % fake_msg['body']


def test_destination_parsing_for_incident():
    hipchat_vendor = iris_hipchat({
        'auth_token': 'abc',
        'iris_incident_url': 'http://foo.bar/incidents',
        'room_id': 1234,
    })
    fake_msg = {
        'application': 'grafana',
        'incident_id': 123,
        'body': 'test body',
        'message_id': 456,
    }
    destination = '1234;testtoken;@user1'
    fake_msg['destination'] = destination
    room_id, token, mention = hipchat_vendor.parse_destination(fake_msg['destination'])

    assert room_id == 1234
    assert token == 'testtoken'
    assert mention == '@user1'

    destination = '1234;testtoken'
    fake_msg['destination'] = destination
    room_id, token, mention = hipchat_vendor.parse_destination(fake_msg['destination'])

    assert room_id == 1234
    assert token == 'testtoken'
    assert mention == ''


def test_destination_parsing_defaults_for_incident():
    hipchat_vendor = iris_hipchat({
        'auth_token': 'validtoken',
        'iris_incident_url': 'http://foo.bar/incidents',
        'room_id': 1234,
    })
    fake_msg = {
        'application': 'grafana',
        'incident_id': 123,
        'body': 'test body',
        'message_id': 456,
    }
    destination = 'user_missing_@'
    fake_msg['destination'] = destination
    room_id, token, mention = hipchat_vendor.parse_destination(fake_msg['destination'])

    assert room_id == 1234
    assert token == 'validtoken'
    assert mention == ''

    destination = 'not_an_int;testtoken'
    fake_msg['destination'] = destination
    room_id, token, mention = hipchat_vendor.parse_destination(fake_msg['destination'])

    assert room_id == 1234
    assert token == 'testtoken'
    assert mention == ''
