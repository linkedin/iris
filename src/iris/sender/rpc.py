# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import os
from gevent import Timeout, socket
from gevent.server import StreamServer
import msgpack
from ..utils import msgpack_unpack_msg_from_socket, sanitize_unicode_dict
from . import cache
from iris import metrics
from iris.role_lookup import IrisRoleLookupException

import logging
import logging.handlers
logger = logging.getLogger(__name__)
access_logger = logging.getLogger('RPC:access')


send_funcs = {}
rpc_timeout = None
rpc_server = None


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
        logging.exception('Failed connecting to %s to send message (ID %s)',
                          pretty_address, message_id)
        metrics.incr('rpc_message_pass_fail_cnt')
        return False

    if sender_resp == 'OK':
        access_logger.info('Successfully passed message (ID %s) to %s for sending',
                           message_id, pretty_address)
        metrics.incr('rpc_message_pass_success_cnt')
        return True
    else:
        logger.error('Failed sending message (ID %s) through %s: %s',
                     message_id, pretty_address, sender_resp)
        metrics.incr('rpc_message_pass_fail_cnt')
        return False


def reject_api_request(socket, address, err_msg):
    logger.info('-> %s %s', address, err_msg)
    socket.sendall(msgpack.packb(err_msg))


def handle_api_notification_request(socket, address, req):
    notification = req['data']
    if 'application' not in notification:
        reject_api_request(socket, address, 'INVALID application')
        logger.warning('Dropping OOB message due to missing application key')
        return
    notification['subject'] = '[%s] %s' % (notification['application'],
                                           notification.get('subject', ''))
    target_list = notification.get('target_list')
    role = notification.get('role')
    if not role and not target_list:
        reject_api_request(socket, address, 'INVALID role')
        logger.warning('Dropping OOB message with invalid role "%s" from app %s',
                       role, notification['application'])
        return
    target = notification.get('target')
    if not (target or target_list):
        reject_api_request(socket, address, 'INVALID target')
        logger.warning('Dropping OOB message with invalid target "%s" from app %s',
                       target, notification['application'])
        return
    expanded_targets = None
    # if role is literal_target skip unrolling
    if not notification.get('unexpanded'):
        # For multi-recipient notifications, pre-populate destination with literal targets,
        # then expand the remaining
        has_literal_target = False
        if target_list:
            expanded_targets = []
            notification['destination'] = []
            notification['bcc_destination'] = []
            for t in target_list:
                role = t['role']
                target = t['target']
                bcc = t.get('bcc')
                try:
                    if role == 'literal_target':
                        if bcc:
                            notification['bcc_destination'].append(target)
                        else:
                            notification['destination'].append(target)
                        has_literal_target = True
                    else:
                        expanded = cache.targets_for_role(role, target)
                        expanded_targets += [{'target': e, 'bcc': bcc} for e in expanded]
                except IrisRoleLookupException:
                    # Maintain best-effort delivery for remaining targets if one fails to resolve
                    continue
        else:
            try:
                expanded_targets = cache.targets_for_role(role, target)
            except IrisRoleLookupException:
                expanded_targets = None
        if not expanded_targets and not has_literal_target:
            reject_api_request(socket, address, 'INVALID role:target')
            logger.warning('Dropping OOB message with invalid role:target "%s:%s" from app %s',
                           role, target, notification['application'])
            return

    sanitize_unicode_dict(notification)

    # If we're rendering this using templates+context instead of body, fill in the
    # needed iris key.
    if 'template' in notification:
        if 'context' not in notification:
            logger.warning('Dropping OOB message due to missing context from app %s',
                           notification['application'])
            reject_api_request(socket, address, 'INVALID context')
            return
        else:
            # fill in dummy iris meta data
            notification['context']['iris'] = {}
    elif 'email_html' in notification:
        if not isinstance(notification['email_html'], str):
            logger.warning('Dropping OOB message with invalid email_html from app %s: %s',
                           notification['application'], notification['email_html'])
            reject_api_request(socket, address, 'INVALID email_html')
            return
    elif 'body' not in notification:
        reject_api_request(socket, address, 'INVALID body')
        logger.warning('Dropping OOB message with invalid body from app %s',
                       notification['application'])
        return

    access_logger.info('-> %s OK, to %s:%s (%s:%s)',
                       address, role, target, notification['application'],
                       notification.get('priority', notification.get('mode', '?')))

    notification_count = 1
    if notification.get('unexpanded'):
        notification['destination'] = notification['target']
        send_funcs['message_send_enqueue'](notification)
    elif notification.get('multi-recipient'):
        notification['target'] = expanded_targets
        send_funcs['message_send_enqueue'](notification)
        notification_count = len(expanded_targets)
    else:
        for _target in expanded_targets:
            temp_notification = notification.copy()
            temp_notification['target'] = _target
            send_funcs['message_send_enqueue'](temp_notification)
    metrics.incr('notification_cnt', inc=notification_count)
    socket.sendall(msgpack.packb('OK'))


def handle_slave_send(socket, address, req):
    message = req['data']
    message_id = message.get('message_id', '?')

    message['to_slave'] = True

    try:
        runtime = send_funcs['message_send_enqueue'](message)
        response = 'OK'
        access_logger.info('Message (ID %s) from master %s queued successfully', message_id, address)
    except Exception:
        response = 'FAIL'
        logger.exception('Queueing message (ID %s) from master %s failed.')
        access_logger.error('Failed queueing message (ID %s) from master %s: %s', message_id, address, runtime)
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
        if not req:
            logger.warning('Couldn\'t get msgpack data from %s', address)
            socket.close()
            return
        access_logger.info('%s %s', address, req['endpoint'])
        handler = api_request_handlers.get(req['endpoint'])
        if handler is not None:
            handler(socket, address, req)
        else:
            logger.info('-> %s unknown request', address)
            socket.sendall(msgpack.packb('UNKNOWN'))
    except Timeout:
        metrics.incr('api_request_timeout_cnt')
        logger.warning('-> %s timeout', address)
        socket.sendall(msgpack.packb('TIMEOUT'))
    finally:
        timeout.cancel()
    socket.close()


def run(sender_config):
    global rpc_server
    try:
        rpc_server = StreamServer((sender_config['host'], sender_config['port']),
                                  handle_api_request)
        rpc_server.start()
        return True
    except Exception:
        logger.exception('Failed binding to sender RPC port')
        return False


def shutdown():
    global rpc_server
    if rpc_server:
        logger.info('Stopping RPC server')
        rpc_server.close()


def init(sender_config, _send_funcs):
    global rpc_timeout

    send_funcs.update(_send_funcs)

    default_rpc_timeout = 20
    try:
        rpc_timeout = int(sender_config.get('rpc_timeout', default_rpc_timeout))
    except ValueError:
        logger.exception('Failed parsing rpc_timeout in config')
        rpc_timeout = default_rpc_timeout
    logger.info('RPC timeout is set to %s seconds', rpc_timeout)

    access_log_cfg = {
        'filename': './access.log',
        'mode': 'a',
        'maxBytes': 104857600,
        'backupCount': 20,
    }
    access_log_cfg.update(sender_config.get('access_log', {}))

    log_dir = os.path.dirname(access_log_cfg['filename'])
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    log_hdl = logging.handlers.RotatingFileHandler(**access_log_cfg)
    log_hdl.setFormatter(formatter)
    access_logger.propagate = False
    access_logger.addHandler(log_hdl)
