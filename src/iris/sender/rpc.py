# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from __future__ import absolute_import

from gevent import Timeout, socket
from gevent.server import StreamServer
from itertools import cycle
import msgpack
from ..utils import msgpack_unpack_msg_from_socket
from . import cache
from .shared import send_queue, add_mode_stat
from iris import metrics

import logging
logger = logging.getLogger(__name__)


sender_slaves = None
num_slaves = 0
send_funcs = {}
rpc_timeout = None


def msgpack_handle_sets(obj):
    if isinstance(obj, set):
        return list(obj)


def generate_msgpack_message_payload(message):
    return msgpack.packb({'endpoint': 'v0/slave_send', 'data': message}, default=msgpack_handle_sets)


def send_message_to_slave(message, address):
    try:
        payload = generate_msgpack_message_payload(message)
    except TypeError:
        logger.exception('Failed encoding message %s as msgpack', message)
        metrics.incr('rpc_message_pass_fail_cnt')
        return False

    pretty_address = '%s:%s' % address
    message_id = message.get('message_id', '?')
    try:
        s = socket.create_connection(address)
        s.send(payload)
        sender_resp = msgpack_unpack_msg_from_socket(s)
        s.close()
    except socket.error:
        logging.exception('Failed connecting to %s to send message (ID %s)', pretty_address, message_id)
        metrics.incr('rpc_message_pass_fail_cnt')
        return False

    if sender_resp == 'OK':
        logger.info('Successfully passed message (ID %s) to %s for sending', message_id, pretty_address)
        metrics.incr('rpc_message_pass_success_cnt')
        return True
    else:
        logger.error('Failed sending message (ID %s) through %s: %s', message_id, pretty_address, sender_resp)
        metrics.incr('rpc_message_pass_fail_cnt')
        return False


def init(sender_config, _send_funcs):
    global sender_slaves, num_slaves, rpc_timeout

    send_funcs.update(_send_funcs)

    default_rpc_timeout = 20
    try:
        rpc_timeout = int(sender_config.get('rpc_timeout', default_rpc_timeout))
    except ValueError:
        logger.exception('Failed parsing rpc_timeout in config')
        rpc_timeout = default_rpc_timeout
    logger.info('RPC timeout is set to %s seconds', rpc_timeout)

    if not sender_config.get('is_master'):
        return

    slave_configs = sender_config.get('slaves', [])
    if slave_configs:
        logger.info('Sender configured with slaves: %s', ', '.join(['%(host)s:%(port)s' % slave for slave in slave_configs]))
        sender_slaves = cycle([(slave['host'], slave['port']) for slave in slave_configs])
        num_slaves = len(slave_configs)
    else:
        logger.info('Sender configured with no slaves')


def reject_api_request(socket, address, err_msg):
    logger.info('-> %s %s', address, err_msg)
    socket.sendall(msgpack.packb(err_msg))


def handle_api_notification_request(socket, address, req):
    notification = req['data']
    notification['subject'] = '[%(application)s] %(subject)s' % notification
    role = notification.get('role')
    if not role:
        reject_api_request(socket, address, 'INVALID role')
        return
    target = notification.get('target')
    if not target:
        reject_api_request(socket, address, 'INVALID target')
        return

    expanded_targets = cache.targets_for_role(role, target)
    if not expanded_targets:
        reject_api_request(socket, address, 'INVALID role:target')
        return

    # If we're rendering this using templates+context instead of body, fill in the
    # needed iris key.
    if notification.get('template') and notification.get('context'):
        notification['context']['iris'] = notification['context'].get('iris', {})

    logger.info('-> %s OK, to %s:%s (%s)',
                address, role, target, notification.get('priority', notification.get('mode', '?')))

    for _target in expanded_targets:
        temp_notification = notification.copy()
        temp_notification['target'] = _target
        send_queue.put(temp_notification)
    metrics.incr('notification_cnt')
    socket.sendall(msgpack.packb('OK'))


def handle_slave_send(socket, address, req):
    message = req['data']
    message_id = message.get('message_id', '?')

    try:
        runtime = send_funcs['send_message'](message)
        add_mode_stat(message['mode'], runtime)

        metrics_key = 'app_%(application)s_mode_%(mode)s_cnt' % message
        metrics.add_new_metrics({metrics_key: 0})
        metrics.incr(metrics_key)

        if runtime is not None:
            response = 'OK'
            logger.info('Message (ID %s) from master %s sent successfully', message_id, address)
            metrics.incr('slave_message_send_success_cnt')
        else:
            response = 'FAIL'
            logger.error('Got falsy value from send_message for message (ID %s) from master %s: %s', message_id, address, runtime)
            metrics.incr('slave_message_send_fail_cnt')
    except Exception:
        response = 'FAIL'
        logger.exception('Sending message (ID %s) from master %s failed.')
        metrics.incr('slave_message_send_fail_cnt')

    socket.sendall(msgpack.packb(response))


api_request_handlers = {
    'v0/send': handle_api_notification_request,
    'v0/slave_send': handle_slave_send
}


def handle_api_request(socket, address):
    metrics.incr('api_request_cnt')
    timeout = Timeout.start_new(rpc_timeout)
    try:
        req = msgpack_unpack_msg_from_socket(socket)
        logger.info('%s %s', address, req['endpoint'])
        handler = api_request_handlers.get(req['endpoint'])
        if handler is not None:
            handler(socket, address, req)
        else:
            logger.info('-> %s unknown request', address)
            socket.sendall(msgpack.packb('UNKNOWN'))
    except Timeout:
        metrics.incr('api_request_timeout_cnt')
        logger.info('-> %s timeout', address)
        socket.sendall(msgpack.packb('TIMEOUT'))
    finally:
        timeout.cancel()
    socket.close()


def run(sender_config):
    StreamServer((sender_config['host'], sender_config['port']),
                 handle_api_request).start()
