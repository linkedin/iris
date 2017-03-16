#!/usr/bin/env python

# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

# -*- coding:utf-8 -*-

from iris_api.bin.sender import init_sender
import msgpack


def test_configure(mocker):
    mocker.patch('iris_api.sender.cache.RoleTargets.initialize_active_targets')
    mocker.patch('iris_api.db.init')
    mocker.patch('iris_api.bin.sender.api_cache.cache_priorities')
    mocker.patch('iris_api.bin.sender.api_cache.cache_applications')
    mocker.patch('iris_api.bin.sender.api_cache.cache_modes')
    init_sender({
        'db': {
            'conn': {
                'kwargs': {
                    'scheme': 'mysql+pymysql',
                    'user': 'foo',
                    'password': 'bar',
                    'host': '127.0.0.1',
                    'database': 'iris',
                    'charset': 'utf8',
                },
                'str': '%(scheme)s://%(user)s:%(password)s@%(host)s/%(database)s?charset=%(charset)s'
            },
            'kwargs': {
                'pool_recycle': 3600,
                'echo': True,
                'pool_size': 100,
                'max_overflow': 100,
                'pool_timeout': 60,
            }
        },
        'sender': {
            'debug': True,
        },
        'oncall': 'http://localhost:8002',
        'role_lookup': 'dummy',
        'metrics': 'dummy',
        'skipsend': True,
        'skipgmailwatch': True,
    })


fake_message = {
    'message_id': 1234,
    'plan_id': 19546,
    'application': 'test-app',
    'priority': 'high',
    'target': 'test-user',
    'mode': 'sms',
}

fake_notification = {
    'application': 'test-app',
    'priority': 'high',
    'target': 'test-user',
    'role': 'user',
    'subject': 'test subject',
}

fake_plan = {
    u'name': u'find-test-user',
    u'threshold_count': 10,
    u'creator': u'test-user',
    u'created': 1470444636,
    u'aggregation_reset': 300,
    u'aggregation_window': 300,
    u'threshold_window': 900,
    u'tracking_type': None,
    u'steps': [
        [{u'repeat': 0, u'target': u'test-user', u'id': 178243, u'priority': u'low', u'step': 1,
          u'role': u'user', u'template': u'test-app Default', u'wait': 0},
         {u'repeat': 1, u'target': u'test-user', u'id': 178252, u'priority': u'high', u'step': 1,
          u'role': u'user', u'template': u'test-app Default', u'wait': 300}],
        [{u'repeat': 3, u'target': u'test-user', u'id': 178261, u'priority': u'urgent', u'step': 2,
          u'role': u'user', u'template': u'test-app Default', u'wait': 900}]
    ],
    u'tracking_template': None,
    u'tracking_key': None,
    u'active': 1,
    u'id': 19546,
    u'description': u"please don't abuse this plan :)"
}


def test_fetch_and_prepare_message(mocker):
    mock_iris_client = mocker.patch('iris_api.sender.cache.iris_client')
    mock_iris_client.get.return_value.json.return_value = fake_plan
    from iris_api.bin.sender import (
        fetch_and_prepare_message, message_queue, send_queue
    )

    # dry out message/send queue
    while message_queue.qsize() > 0:
        message_queue.get()
    while send_queue.qsize() > 0:
        send_queue.get()
    message_queue.put(fake_message)

    fetch_and_prepare_message()

    assert message_queue.qsize() == 0
    assert send_queue.qsize() == 1
    m = send_queue.get()
    assert m['message_id'] == fake_message['message_id']


def test_fetch_and_send_message(mocker):
    def check_mark_message_sent(m):
        assert m['message_id'] == fake_message['message_id']

    def mock_set_target_contact(message):
        message['destination'] = 'foo@example.com'
        message['mode'] = 'email'
        message['mode_id'] = 1
        return True

    mocker.patch('iris_api.bin.sender.db')
    mocker.patch('iris_api.bin.sender.send_message').return_value = 1
    mocker.patch('iris_api.bin.sender.quota')
    mocker.patch('iris_api.bin.sender.update_message_mode')
    mock_mark_message_sent = mocker.patch('iris_api.bin.sender.mark_message_as_sent')
    mock_mark_message_sent.side_effect = check_mark_message_sent
    mocker.patch('iris_api.bin.sender.set_target_contact').side_effect = mock_set_target_contact
    mock_iris_client = mocker.patch('iris_api.sender.cache.iris_client')
    mock_iris_client.get.return_value.json.return_value = fake_plan
    from iris_api.bin.sender import (
        fetch_and_send_message, send_queue
    )

    # dry out send queue
    while send_queue.qsize() > 0:
        send_queue.get()
    send_queue.put(fake_message)

    fetch_and_send_message()

    assert send_queue.qsize() == 0
    mock_mark_message_sent.assert_called_once()


def test_handle_api_request_v0_send(mocker):
    from iris_api.sender.rpc import handle_api_request
    from iris_api.sender.shared import send_queue

    # support expanding target
    mocker.patch('iris_api.sender.cache.RoleTargets.__call__', lambda _, role, target: [target])

    mock_address = mocker.MagicMock()
    mock_socket = mocker.MagicMock()
    mock_socket.recv.return_value = msgpack.packb({
        'endpoint': 'v0/send',
        'data': fake_notification,
    })

    while send_queue.qsize() > 0:
        send_queue.get()

    handle_api_request(mock_socket, mock_address)

    assert send_queue.qsize() == 1
    m = send_queue.get()
    assert m['subject'] == '[%s] %s' % (fake_notification['application'],
                                        fake_notification['subject'])


def test_handle_api_request_v0_send_with_mode(mocker):
    from iris_api.sender.rpc import handle_api_request
    from iris_api.sender.shared import send_queue

    # support expanding target
    mocker.patch('iris_api.sender.cache.RoleTargets.__call__', lambda _, role, target: [target])
    mocker.patch('iris_api.bin.sender.set_target_contact')

    fake_mode_notification = {}
    fake_mode_notification.update(fake_notification)
    fake_mode_notification['mode'] = 'sms'

    mock_address = mocker.MagicMock()
    mock_socket = mocker.MagicMock()
    mock_socket.recv.return_value = msgpack.packb({
        'endpoint': 'v0/send',
        'data': fake_mode_notification,
    })

    while send_queue.qsize() > 0:
        send_queue.get()

    handle_api_request(mock_socket, mock_address)

    assert send_queue.qsize() == 1
    m = send_queue.get()
    assert m['subject'] == '[%s] %s' % (fake_mode_notification['application'],
                                        fake_mode_notification['subject'])


def test_handle_api_request_v0_send_timeout(mocker):
    import iris_api.sender.rpc
    iris_api.sender.rpc.rpc_timeout = 5

    def slee_10(x):
        from gevent import sleep
        sleep(10)

    mock_address = mocker.MagicMock()
    mock_socket = mocker.MagicMock()
    mock_socket.recv.side_effect = slee_10

    iris_api.sender.rpc.handle_api_request(mock_socket, mock_address)

    mock_socket.sendall.called_with(msgpack.packb('TIMEOUT'))


def test_render_email_response_message(mocker):
    from iris_api.bin.sender import render
    mock_cursor = mocker.MagicMock()
    mock_db = mocker.patch('iris_api.bin.sender.db')
    mock_db.engine.raw_connection().cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = ['bar', 'foo']

    mock_message = {'message_id': 1}
    render(mock_message)

    mock_cursor.execute.assert_called_once_with('SELECT `body`, `subject` FROM `message` WHERE `id` = %s', 1)
    assert mock_message['body'] == 'bar'
    assert mock_message['subject'] == 'foo'


def test_msgpack_handle_sets():
    from iris_api.sender.rpc import msgpack_handle_sets
    assert msgpack_handle_sets(set([1, 2, 3, 4])) == [1, 2, 3, 4]


def test_generate_slave_message_payload():
    from iris_api.sender.rpc import generate_msgpack_message_payload
    data = {
        'ids': set([1, 2, 3, 4])
    }
    result = generate_msgpack_message_payload(data)
    assert msgpack.unpackb(result) == {
        'endpoint': 'v0/slave_send',
        'data': {
            'ids': [1, 2, 3, 4]
        }
    }


def test_quotas(mocker):
    from iris_api.sender.quota import ApplicationQuota
    from iris_api.metrics import stats
    from gevent import sleep
    mocker.patch('iris_api.sender.quota.ApplicationQuota.get_new_rules', return_value=[(u'testapp', 5, 2, 120, 120, u'testuser', u'user', u'iris-plan', 10)])
    mocker.patch('iris_api.sender.quota.ApplicationQuota.notify_incident')
    mocker.patch('iris_api.sender.quota.ApplicationQuota.notify_target')
    quotas = ApplicationQuota(None, None, None)
    sleep(1)
    assert quotas.allow_send({'application': 'testapp'})
    assert quotas.allow_send({'application': 'testapp'})
    assert quotas.allow_send({'application': 'testapp'})  # Breach soft quota
    assert quotas.allow_send({'application': 'testapp'})
    assert quotas.allow_send({'application': 'testapp'})
    assert not quotas.allow_send({'application': 'testapp'})  # Breach hard quota
    assert not quotas.allow_send({'application': 'testapp'})
    assert stats['quota_soft_exceed_cnt'] == 3
    assert stats['quota_hard_exceed_cnt'] == 2

    assert stats['app_testapp_quota_hard_usage_pct'] == 100
    assert stats['app_testapp_quota_soft_usage_pct'] == 200

    for _ in xrange(10):
        assert quotas.allow_send({'application': 'app_without_quota'})
