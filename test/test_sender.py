#!/usr/bin/env python

# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

# -*- coding:utf-8 -*-

import time
from iris.bin.sender import init_sender
import msgpack


def test_configure(mocker):
    mocker.patch('iris.sender.cache.RoleTargets.initialize_active_targets')
    mocker.patch('iris.db.init')
    mocker.patch('iris.bin.sender.api_cache.cache_priorities')
    mocker.patch('iris.bin.sender.api_cache.cache_applications')
    mocker.patch('iris.bin.sender.api_cache.cache_modes')
    mock_iris_client = mocker.MagicMock()
    mocker.patch('iris.sender.cache.IrisClient').return_value = mock_iris_client
    mock_iris_client.get.return_value.status_code = 200

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
    'body': 'test body',
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


def init_queue_with_item(queue, item=None):
    # drain out queue
    while queue.qsize() > 0:
        queue.get()
    if item:
        queue.put(item)


def test_fetch_and_prepare_message(mocker):
    mock_iris_client = mocker.patch('iris.sender.cache.iris_client')
    mock_iris_client.get.return_value.json.return_value = fake_plan
    from iris.bin.sender import (
        fetch_and_prepare_message, message_queue, send_queue
    )

    init_queue_with_item(message_queue, fake_message)
    init_queue_with_item(send_queue)

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

    mocker.patch('iris.bin.sender.db')
    mocker.patch('iris.bin.sender.send_message').return_value = 1
    mocker.patch('iris.bin.sender.quota')
    mocker.patch('iris.bin.sender.update_message_mode')
    mock_mark_message_sent = mocker.patch('iris.bin.sender.mark_message_as_sent')
    mock_mark_message_sent.side_effect = check_mark_message_sent
    mocker.patch('iris.bin.sender.set_target_contact').side_effect = mock_set_target_contact
    mock_iris_client = mocker.patch('iris.sender.cache.iris_client')
    mock_iris_client.get.return_value.json.return_value = fake_plan
    from iris.bin.sender import (
        fetch_and_send_message, send_queue
    )

    # drain out send queue
    while send_queue.qsize() > 0:
        send_queue.get()
    send_queue.put(fake_message)

    fetch_and_send_message()

    assert send_queue.qsize() == 0
    mock_mark_message_sent.assert_called_once()


def test_no_valid_modes(mocker):
    def check_mark_message_sent(m):
        assert m['message_id'] == fake_message['message_id']

    def mock_set_target_contact(message):
        return False

    mocker.patch('iris.bin.sender.db')
    mock_mark_message_no_contact = mocker.patch('iris.bin.sender.mark_message_has_no_contact')
    mock_mark_message_sent = mocker.patch('iris.bin.sender.mark_message_as_sent')
    mock_mark_message_sent.side_effect = check_mark_message_sent
    mocker.patch('iris.bin.sender.set_target_contact').side_effect = mock_set_target_contact
    mock_iris_client = mocker.patch('iris.sender.cache.iris_client')
    mock_iris_client.get.return_value.json.return_value = fake_plan
    from iris.bin.sender import (
        fetch_and_send_message, send_queue
    )

    # drain out send queue
    while send_queue.qsize() > 0:
        send_queue.get()
    send_queue.put(fake_message)

    fetch_and_send_message()

    assert send_queue.qsize() == 0
    assert not mock_mark_message_sent.called
    mock_mark_message_no_contact.assert_called_once()


def test_handle_api_request_v0_send(mocker):
    from iris.sender.rpc import handle_api_request
    from iris.sender.shared import send_queue

    # support expanding target
    mocker.patch('iris.sender.cache.RoleTargets.__call__', lambda _, role, target: [target])

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
    from iris.sender.rpc import handle_api_request
    from iris.sender.shared import send_queue

    # support expanding target
    mocker.patch('iris.sender.cache.RoleTargets.__call__', lambda _, role, target: [target])
    mocker.patch('iris.bin.sender.set_target_contact')

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
    import iris.sender.rpc
    iris.sender.rpc.rpc_timeout = 5

    def slee_10(x):
        from gevent import sleep
        sleep(10)

    mock_address = mocker.MagicMock()
    mock_socket = mocker.MagicMock()
    mock_socket.recv.side_effect = slee_10

    iris.sender.rpc.handle_api_request(mock_socket, mock_address)

    mock_socket.sendall.assert_called_with(msgpack.packb('TIMEOUT'))


def test_render_email_response_message(mocker):
    from iris.bin.sender import render
    mock_cursor = mocker.MagicMock()
    mock_db = mocker.patch('iris.bin.sender.db')
    mock_db.engine.raw_connection().cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = ['bar', 'foo']

    mock_message = {'message_id': 1}
    render(mock_message)

    mock_cursor.execute.assert_called_once_with('SELECT `body`, `subject` FROM `message` WHERE `id` = %s', 1)
    assert mock_message['body'] == 'bar'
    assert mock_message['subject'] == 'foo'


def test_msgpack_handle_sets():
    from iris.sender.rpc import msgpack_handle_sets
    assert msgpack_handle_sets(set([1, 2, 3, 4])) == [1, 2, 3, 4]


def test_generate_slave_message_payload():
    from iris.sender.rpc import generate_msgpack_message_payload
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
    from iris.sender.quota import ApplicationQuota
    from iris.metrics import stats
    from gevent import sleep
    mocker.patch('iris.sender.quota.ApplicationQuota.get_new_rules',
                 return_value=[(
                     u'testapp', 5, 2, 120, 120, u'testuser',
                     u'user', u'iris-plan', 10
                 )])
    mocker.patch('iris.sender.quota.ApplicationQuota.notify_incident')
    mocker.patch('iris.sender.quota.ApplicationQuota.notify_target')
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


def test_aggregate_audit_msg(mocker):
    mock_iris_client = mocker.patch('iris.sender.cache.iris_client')
    mock_iris_client.get.return_value.json.return_value = fake_plan
    from iris.bin.sender import (
        fetch_and_prepare_message, message_queue, send_queue,
        plan_aggregate_windows
    )

    init_queue_with_item(message_queue, fake_message)
    init_queue_with_item(send_queue)

    now = time.time()
    msg_aggregate_key = (
        fake_message['plan_id'],
        fake_message['application'],
        fake_message['priority'],
        fake_message['target'])
    from collections import defaultdict
    plan_aggregate_windows[msg_aggregate_key] = defaultdict(int)
    plan_aggregate_windows[msg_aggregate_key][now] = 10
    plan_aggregate_windows[msg_aggregate_key][now - 60] = 10

    mocker.patch('iris.bin.sender.cache').plans = {fake_plan['id']: fake_plan}

    mocker.patch('iris.bin.sender.spawn')
    from iris.bin.sender import spawn as mock_spawn

    # run code to test
    fetch_and_prepare_message()

    # examine results
    assert send_queue.qsize() == 0
    from iris.sender import auditlog
    mock_spawn.assert_called_with(
        auditlog.message_change,
        fake_message['message_id'],
        auditlog.SENT_CHANGE,
        '',
        '',
        "Aggregated with key (19546, 'test-app', 'high', 'test-user')")


def test_handle_api_notification_request_invalid_message(mocker):
    from iris.sender.rpc import handle_api_notification_request
    mock_socket = mocker.MagicMock()
    handle_api_notification_request(mock_socket, mocker.MagicMock(), {
        'data': {
            'application': 'test_app',
        }
    })
    mock_socket.sendall.assert_called_with(msgpack.packb('INVALID role'))

    handle_api_notification_request(mock_socket, mocker.MagicMock(), {
        'data': {
            'role': 'user',
            'application': 'test_app',
        }
    })
    mock_socket.sendall.assert_called_with(msgpack.packb('INVALID target'))

    mocker.patch('iris.sender.rpc.cache').targets_for_role.return_value = ['foo']
    handle_api_notification_request(mock_socket, mocker.MagicMock(), {
        'data': {
            'target': 'foo',
            'role': 'user',
            'application': 'test_app',
        }
    })
    mock_socket.sendall.assert_called_with(msgpack.packb('INVALID body'))

    handle_api_notification_request(mock_socket, mocker.MagicMock(), {
        'data': {
            'target': 'foo',
            'role': 'user',
            'application': 'test_app',
            'template': 'test',
        }
    })
    mock_socket.sendall.assert_called_with(msgpack.packb('INVALID context'))

    # should work when user is setting body key
    handle_api_notification_request(mock_socket, mocker.MagicMock(), {
        'data': {
            'target': 'foo',
            'role': 'user',
            'application': 'test_app',
            'body': 'test',
        }
    })
    mock_socket.sendall.assert_called_with(msgpack.packb('OK'))

    # should work when user is setting template key
    handle_api_notification_request(mock_socket, mocker.MagicMock(), {
        'data': {
            'target': 'foo',
            'role': 'user',
            'application': 'test_app',
            'template': 'test',
            'context': {},
        }
    })
    mock_socket.sendall.assert_called_with(msgpack.packb('OK'))

    # should work when user is setting email_html key
    handle_api_notification_request(mock_socket, mocker.MagicMock(), {
        'data': {
            'target': 'foo',
            'role': 'user',
            'application': 'test_app',
            'email_html': '<p>test</p>',
        }
    })
    mock_socket.sendall.assert_called_with(msgpack.packb('OK'))

    from iris.bin.sender import send_queue
    # drain out send queue
    while send_queue.qsize() > 0:
        send_queue.get()


def test_sanitize_unicode_dict():
    import pytest
    from jinja2.sandbox import SandboxedEnvironment
    from iris.utils import sanitize_unicode_dict

    # Use jinja the same way as in sender
    env = SandboxedEnvironment(autoescape=False)
    template = env.from_string('{{var}} {{var2}}')
    bad_context = {'var': '\xe2\x80\x99', 'var2': 2}

    with pytest.raises(UnicodeDecodeError):
        template.render(**bad_context)

    template.render(**sanitize_unicode_dict(bad_context))
