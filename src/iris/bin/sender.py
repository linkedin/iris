# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from gevent import monkey, sleep, spawn, queue
monkey.patch_all()  # NOQA

import logging
import logging.handlers
import time
import ujson
import os
import socket
import gevent
import signal
import setproctitle
import copy

from collections import defaultdict
from iris.plugins import init_plugins
from iris.vendors import IrisVendorManager, iris_smtp
from iris.sender import auditlog
from iris import metrics
from uuid import uuid4
from iris.gmail import Gmail
from iris import db
from iris.api import load_config
from iris.utils import sanitize_unicode_dict
from iris.sender import rpc, cache
from iris.sender.message import update_message_mode
from iris.sender.oneclick import oneclick_email_markup, generate_oneclick_url
from iris import cache as api_cache
from iris.sender.quota import ApplicationQuota
from iris.role_lookup import IrisRoleLookupException
from pymysql import DataError
# queue for sending messages
from iris.sender.shared import per_mode_send_queues, add_mode_stat

# sql

NEW_INCIDENTS = '''SELECT
    `incident`.`id` as `id`,
    `incident`.`created` as `created`,
    `incident`.`plan_id` as `plan_id`,
    `incident`.`context` as `context`,
    `application`.`name` as `application`
FROM `incident`
JOIN `application`
ON `incident`.`application_id`=`application`.`id`
WHERE `current_step`=0 AND `active`=1'''

INACTIVE_SQL = '''UPDATE
`incident`
SET `active`=0
WHERE `id` IN %s'''

GET_INACTIVE_IDS_SQL = '''SELECT
distinct `incident_id`
FROM (
    SELECT
        `incident_id`,
        `max`,
        `age`,
        MAX(`count`) as max_count
        FROM (
            SELECT
            `message`.`incident_id` as `incident_id`,
            `message`.`plan_notification_id` as `plan_notification_id`,
            count(`message`.`id`) as `count`,
            `plan_notification`.`repeat` + 1 as `max`,
            TIMESTAMPDIFF(SECOND, MAX(`message`.`sent`), NOW()) as `age`,
            `plan_notification`.`wait` as `wait`,
            `plan_notification`.`step` as `step`,
            `incident`.`current_step`,
            `plan`.`step_count`,
            `message`.`plan_id`,
            `message`.`application_id`,
            `incident`.`context`
            FROM `message`
            JOIN `incident` ON `message`.`incident_id` = `incident`.`id`
            JOIN `plan_notification` ON `message`.`plan_notification_id` = `plan_notification`.`id`
            JOIN `plan` ON `message`.`plan_id` = `plan`.`id`
            WHERE `incident`.`active` = 1
            AND `incident`.`current_step`=`plan`.`step_count`
            AND `step` = `incident`.`current_step`
            GROUP BY `incident`.`id`, `message`.`plan_notification_id`, `message`.`target_id`
        ) as `inner`
        GROUP BY `incident_id`, `plan_notification_id`
        HAVING `max_count` = `max` AND BIT_AND(`age` > `wait`) = 1
    ) as `exhausted_incidents`'''

QUEUE_SQL = '''SELECT
`incident_id`,
`plan_id`,
`plan_notification_id`,
max(`count`) as `count`,
`max`,
`age`,
`wait`,
`step`,
`current_step`,
`step_count`
FROM (
    SELECT
        `message`.`incident_id` as `incident_id`,
        `message`.`plan_notification_id` as `plan_notification_id`,
        count(`message`.`id`) as `count`,
        `plan_notification`.`repeat` + 1 as `max`,
        TIMESTAMPDIFF(SECOND, max(`message`.`created`), NOW()) as `age`,
        `plan_notification`.`wait` as `wait`,
        `plan_notification`.`step` as `step`,
        `incident`.`current_step`,
        `plan`.`step_count`,
        `message`.`plan_id`,
        `message`.`application_id`,
        `incident`.`context`
    FROM `message`
    JOIN `incident` ON `message`.`incident_id` = `incident`.`id`
    JOIN `plan_notification` ON `message`.`plan_notification_id` = `plan_notification`.`id`
    JOIN `plan` ON `message`.`plan_id` = `plan`.`id`
    WHERE `incident`.`active` = 1
    GROUP BY `incident`.`id`, `message`.`plan_notification_id`, `message`.`target_id`
) as `inner`
GROUP BY `incident_id`, `plan_notification_id`
HAVING `age` > `wait` AND (`count` < `max`
                           OR (`count` = `max` AND `step` = `current_step`
                               AND `step` < `step_count`))'''

UPDATE_INCIDENT_SQL = '''UPDATE `incident` SET `current_step`=%s WHERE `id`=%s'''

INVALIDATE_INCIDENT = '''UPDATE `incident` SET `active`=0 WHERE `id`=%s'''

INSERT_MESSAGE_SQL = '''INSERT INTO `message`
    (`created`, `plan_id`, `plan_notification_id`, `incident_id`, `application_id`, `target_id`, `priority_id`, `body`)
VALUES (NOW(), %s,%s,%s,%s,%s,%s,%s)'''

BATCH_INSERT_MESSAGE_QUERY = '''INSERT INTO `message`
    (`created`, `plan_id`, `plan_notification_id`, `incident_id`, `application_id`, `target_id`, `priority_id`, `body`)
VALUES '''

UNSENT_MESSAGES_SQL = '''SELECT
    `message`.`body`,
    `message`.`id` as `message_id`,
    `target`.`name` as `target`,
    `priority`.`name` as `priority`,
    `priority`.`id` as `priority_id`,
    `application`.`name` as `application`,
    `plan`.`name` as `plan`,
    `plan`.`id` as `plan_id`,
    `incident`.`id` as `incident_id`,
    `incident`.`context` as `context`,
    `incident`.`created` as `incident_created`,
    `plan_notification`.`template` as `template`,
    `dynamic_target`.`name` as `dynamic_target`
FROM `message`
JOIN `application` ON `message`.`application_id`=`application`.`id`
JOIN `priority` ON `message`.`priority_id`=`priority`.`id`
LEFT OUTER JOIN `target` ON `message`.`target_id`=`target`.`id`
LEFT OUTER JOIN `plan` ON `message`.`plan_id`=`plan`.`id`
LEFT OUTER JOIN `plan_notification` ON `message`.`plan_notification_id`=`plan_notification`.`id`
LEFT OUTER JOIN `incident` ON `message`.`incident_id`=`incident`.`id`
LEFT OUTER JOIN `dynamic_plan_map` ON `incident`.`id` = `dynamic_plan_map`.`incident_id`
  AND `plan_notification`.`dynamic_index` = `dynamic_plan_map`.`dynamic_index`
LEFT OUTER JOIN `target` `dynamic_target` ON `dynamic_target`.`id` = `dynamic_plan_map`.`target_id`
WHERE `message`.`active`=1'''

SENT_MESSAGE_BATCH_SQL = '''UPDATE `message`
SET `destination`=%%s,
    `mode_id`=%%s,
    `template_id`=%%s,
    `batch`=%%s,
    `active`=FALSE,
    `sent`=NOW()
WHERE `id` IN %s'''

SENT_MESSAGE_SQL = '''UPDATE `message`
SET `destination`=%s,
    `mode_id`=%s,
    `template_id`=%s,
    `active`=FALSE,
    `sent`=NOW()
WHERE `id`=%s'''

UPDATE_MESSAGE_BODY_SQL = '''UPDATE `message`
                             SET `body`=%s,
                                 `subject`=%s
                             WHERE `id` IN %s'''

PRUNE_OLD_AUDIT_LOGS_SQL = '''DELETE FROM `message_changelog` WHERE `date` < DATE_SUB(CURDATE(), INTERVAL 3 MONTH)'''

# When a rendered message body is longer than this number of characters, drop it.
MAX_MESSAGE_BODY_LENGTH = 40000
MAX_MESSAGE_RETRIES = 2

# logging
logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
log_file = os.environ.get('SENDER_LOG_FILE')
if log_file:
    ch = logging.handlers.RotatingFileHandler(log_file, mode='a', maxBytes=10485760, backupCount=10)
else:
    ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(ch)

pidfile = os.environ.get('SENDER_PIDFILE')
if pidfile:
    try:
        pid = os.getpid()
        with open(pidfile, 'w') as h:
            h.write('%s\n' % pid)
            logger.info('Wrote pid %s to %s', pid, pidfile)
    except IOError:
        logger.exception('Failed writing pid to %s', pidfile)


# rate limiting data structure message key -> minute -> count
# used to calcuate if a new message exceeds the rate limit
# and needs to be queued
plan_aggregate_windows = {}

# all messages waiting to be queue across all keys
messages = {}

# queue of message_ids waiting to be sent for a given key
queues = {}

# time last message was queued while in aggregation mode for a given key
# used to determine if a new message should be aggregated or if aggregation should end
aggregation = {}

# last time a batch was sent for a given key
# used to determine if it's time to send the next batch
sent = {}

# queue for messages entering the system
# this sets the ground work for not having to poll the DB for messages
message_queue = queue.Queue()

# Quota object used for rate limiting
quota = None

# Coordinator object for sender master election
coordinator = None

# Mode -> [{'greenlet': greenlet, 'kill_set': gevent.Event}]
worker_tasks = defaultdict(list)

# MX -> [{'greenlet': greenlet, 'kill_set': gevent.Event}]
autoscale_email_worker_tasks = defaultdict(list)

# support the 2nd control+c force exiting sender without waiting for tasks to finish
shutdown_started = False

# Set of active message IDs currently being sent, to avoid re-sending messages that are currently
# just blocked on a downstream such as smtp
message_ids_being_sent = set()


default_sender_metrics = {
    'email_cnt': 0, 'email_total': 0, 'email_fail': 0, 'email_sent': 0, 'email_max': 0,
    'email_min': 0, 'email_avg': 0, 'im_cnt': 0, 'im_total': 0, 'im_fail': 0, 'im_sent': 0,
    'im_max': 0, 'im_min': 0, 'im_avg': 0, 'slack_cnt': 0, 'slack_total': 0, 'slack_fail': 0,
    'slack_sent': 0, 'slack_max': 0, 'slack_min': 0, 'slack_avg': 0, 'drop_cnt': 0,
    'drop_total': 0, 'drop_fail': 0, 'drop_sent': 0, 'drop_max': 0, 'drop_min': 0, 'drop_avg': 0,
    'sms_cnt': 0, 'sms_total': 0, 'sms_fail': 0, 'sms_sent': 0, 'sms_max': 0,
    'sms_min': 0, 'sms_avg': 0, 'call_cnt': 0, 'call_total': 0,
    'call_fail': 0, 'call_sent': 0, 'call_max': 0, 'call_min': 0, 'call_avg': 0, 'task_failure': 0,
    'oncall_error': 0, 'role_target_lookup_error': 0, 'target_not_found': 0, 'message_send_cnt': 0,
    'notification_cnt': 0, 'api_request_cnt': 0, 'api_request_timeout_cnt': 0,
    'rpc_message_pass_success_cnt': 0, 'rpc_message_pass_fail_cnt': 0,
    'slave_message_send_success_cnt': 0, 'slave_message_send_fail_cnt': 0,
    'msg_drop_length_cnt': 0, 'send_queue_gets_cnt': 0, 'send_queue_puts_cnt': 0, 'send_queue_puts_fail_cnt': 0,
    'send_queue_email_size': 0, 'send_queue_im_size': 0, 'send_queue_slack_size': 0, 'send_queue_call_size': 0,
    'send_queue_sms_size': 0, 'send_queue_drop_size': 0, 'new_incidents_cnt': 0, 'workers_respawn_cnt': 0,
    'message_retry_cnt': 0, 'message_ids_being_sent_cnt': 0, 'notifications': 0, 'deactivation': 0,
    'new_msg_count': 0, 'poll': 0, 'queue': 0, 'aggregations': 0, 'hipchat_cnt': 0, 'hipchat_fail': 0,
    'hipchat_total': 0, 'hipchat_sent': 0, 'hipchat_max': 0, 'hipchat_min': 0
}

# TODO: make this configurable
target_fallback_mode = 'email'
should_mock_gwatch_renewer = False
config = None


# msg_info takes the form [(incident_id, plan_notification_id), ...]
def create_messages(msg_info):
    msg_count = 0
    query_params = []
    values_count = 0
    error_incident_ids = set()
    connection = db.engine.raw_connection()
    cursor = connection.cursor()

    for (incident_id, plan_notification_id) in msg_info:
        application_id = cache.incidents[incident_id]['application_id']
        plan_notification = cache.plan_notifications[plan_notification_id]
        if plan_notification['role_id'] is None and plan_notification['target_id'] is None:
            dynamic_info = cache.dynamic_plan_map[incident_id][plan_notification['dynamic_index']]
            role = cache.roles[dynamic_info['role_id']]['name']
            target = cache.targets[dynamic_info['target_id']]['name']
        else:
            role = cache.roles[plan_notification['role_id']]['name']
            target = cache.targets[plan_notification['target_id']]['name']

        # find role/priority from plan_notification_id
        try:
            names = cache.targets_for_role(role, target)
        except IrisRoleLookupException as e:
            names = None
            metrics.incr('role_target_lookup_error')
            lookup_fail_reason = str(e)
        else:
            lookup_fail_reason = None

        priority_id = plan_notification['priority_id']
        redirect_to_plan_owner = False
        body = ''

        if not names:

            # if message is optional don't bother the creator, simply return true instead
            if plan_notification['optional']:
                msg_count += 1
                continue

            # Try to get creator of the plan and nag them instead
            name = None
            try:
                name = cache.plans[plan_notification['plan_id']]['creator']
            except (KeyError, TypeError):
                pass

            if not name:
                logger.error(('Failed to find targets for incident %s, plan_notification_id: %s, '
                              'role: %s, target: %s, result: %s and failed looking '
                              'up the plan\'s creator'),
                             incident_id, plan_notification_id, role, target, names)
                error_incident_ids.add(incident_id)
                continue

            try:
                priority_id = api_cache.priorities['low']['id']
            except KeyError:
                logger.error(('Failed to find targets for incident %s, plan_notification_id: %s, '
                              'role: %s, target: %s, result: %s and failed looking '
                              'up ID for low priority'),
                             incident_id, plan_notification_id, role, target, names)
                error_incident_ids.add(incident_id)
                continue

            logger.error(('Failed to find targets for incident %s, plan_notification_id: %s, '
                          'role: %s, target: %s, result: %s. '
                          'Reaching out to %s instead and lowering priority to low (%s)'),
                         incident_id, plan_notification_id, role, target, names, name, priority_id)

            body = ('You are receiving this as you created this plan and we can\'t resolve'
                    ' %s of %s at this time%s.\n\n') % (role, target, ': %s' % lookup_fail_reason if lookup_fail_reason else '')

            names = [name]
            redirect_to_plan_owner = True

        for name in names:
            t = cache.target_names[name]
            if t:
                target_id = t['id']
                # Create message now if it needs to be redirected, otherwise save it for one batched operation
                if not redirect_to_plan_owner:
                    query_params += [plan_notification['plan_id'], plan_notification_id, incident_id,
                                     application_id, target_id, priority_id, body]
                    values_count += 1
                else:
                    retries = 0
                    max_retries = 5
                    while True:
                        retries += 1
                        try:
                            cursor.execute(INSERT_MESSAGE_SQL,
                                           (plan_notification['plan_id'], plan_notification_id, incident_id,
                                            application_id, target_id, priority_id, body))
                            connection.commit()
                        except Exception:
                            logger.warning('Failed inserting message for incident %s. (Try %s/%s)', incident_id, retries, max_retries)
                            if retries < max_retries:
                                sleep(.2)
                                continue
                            else:
                                raise Exception('Failed inserting message retries exceeded')
                        else:
                            # needed for the lastrowid to exist in the DB to satisfy the constraint
                            auditlog.message_change(
                                cursor.lastrowid,
                                auditlog.TARGET_CHANGE,
                                role + '|' + target,
                                name,
                                lookup_fail_reason or 'Changing target to plan owner as we failed resolving original target')
                            break

                msg_count += 1
            else:
                metrics.incr('target_not_found')
                logger.warning('Failed to notify plan creator; no active target found: %s', name)
    if values_count > 0:
        retries = 0
        max_retries = 5
        while True:
            retries += 1
            try:
                msg_sql = BATCH_INSERT_MESSAGE_QUERY + ','.join('(NOW(), %s,%s,%s,%s,%s,%s,%s)' for i in range(values_count))
                cursor.execute(msg_sql, query_params)
                connection.commit()
            except Exception:
                logger.warning('Failed inserting batch messages for incident %s. (Try %s/%s)', incident_id, retries, max_retries)
                if retries < max_retries:
                    sleep(.2)
                    continue
                else:
                    raise Exception('Failed inserting batch messages retries exceeded')
            else:
                msg_count += cursor.rowcount
                break
    cursor.close()
    connection.close()
    return msg_count, error_incident_ids


def deactivate():
    # deactivate incidents that have expired
    logger.info('[-] start deactivate task...')
    start_deactivation = time.time()

    connection = db.engine.raw_connection()
    cursor = connection.cursor()

    max_retries = 3

    # this deadlocks sometimes. try until it doesn't.
    for i in range(1, max_retries + 1):
        try:
            cursor.execute(GET_INACTIVE_IDS_SQL)
            ids = tuple(r[0] for r in cursor)
            if ids:
                cursor.execute(INACTIVE_SQL, (ids,))
                connection.commit()
                break
        except Exception:
            if i == max_retries:
                logger.warning('Failed running deactivate query. (Try %s/%s)', i, max_retries)
            else:
                logger.warning('Deadlocked running deactivate query. (Try %s/%s)', i, max_retries)
            sleep(.2)

    cursor.close()
    connection.close()

    metrics.set('deactivation', time.time() - start_deactivation)
    logger.info('[*] deactivate task finished')


def escalate():
    # make notifications for things that should repeat or escalate
    logger.info('[-] start escalate task...')

    # first, handle new incidents
    start_notifications = time.time()

    connection = db.engine.raw_connection()
    cursor = connection.cursor()
    cursor.execute(NEW_INCIDENTS)

    escalations = {}
    for incident_id, created, plan_id, context, application in cursor:
        escalations[incident_id] = (plan_id, 1)
        # create tracking message if configured
        plan = cache.plans[plan_id]
        tracking_type = plan['tracking_type']
        tracking_key = plan['tracking_key']
        tracking_template = plan['tracking_template']
        app_tracking_template = tracking_template.get(application) if tracking_template else None
        if tracking_type and tracking_key and app_tracking_template:
            # plan defines tracking notifications
            context = ujson.loads(context)
            context['iris'] = {
                'incident_id': incident_id,
                'plan': plan['name'],
                'plan_id': plan_id,
                'application': application,
                'incident_created': created,
            }
            if tracking_type == 'email':
                tracking_message = {
                    'noreply': True,
                    'destination': tracking_key,
                    'mode': tracking_type
                }

                try:
                    subject = app_tracking_template['email_subject'].render(**context)
                except Exception as e:
                    subject = 'plan %s - tracking notification subject failed to render: %s' % (plan['name'], e)
                    logger.exception(subject)
                tracking_message['email_subject'] = subject

                try:
                    body = app_tracking_template['email_text'].render(**context)
                except Exception as e:
                    body = 'plan %s - tracking notification body failed to render: %s' % (plan['name'], e)
                    logger.exception(body)
                tracking_message['email_text'] = body

                email_html_tpl = app_tracking_template.get('email_html')
                if email_html_tpl:
                    try:
                        html_body = email_html_tpl.render(**context)
                    except Exception as e:
                        html_body = 'plan %s - tracking notification html body failed to render: %s' % (plan['name'], e)
                        logger.exception(html_body)
                    tracking_message['email_html'] = html_body
            else:
                tracking_message = {
                    'noreply': True,
                    'destination': tracking_key,
                    'mode': tracking_type
                }
                try:
                    body = app_tracking_template['body'].render(**context)
                except Exception as e:
                    body = 'plan %s - tracking notification body failed to render: %s' % (plan['name'], e)
                    logger.exception(body)
                tracking_message['body'] = body

            message_send_enqueue(tracking_message)
    cursor.close()

    new_incidents_count = len(escalations)
    metrics.set('new_incidents_cnt', new_incidents_count)
    logger.info('[*] %s new incidents', new_incidents_count)

    # then, fetch message count for current incidents
    msg_count = 0
    cursor = connection.cursor(db.dict_cursor)
    cursor.execute(QUEUE_SQL)
    msg_info = []
    for n in cursor.fetchall():
        if n['count'] < n['max']:
            msg_info.append((n['incident_id'], n['plan_notification_id']))
        else:
            escalations[n['incident_id']] = (n['plan_id'], n['current_step'] + 1)
    msg_count += create_messages(msg_info)[0]

    # Create escalation messages
    msg_info = []
    for incident_id, (plan_id, step) in escalations.items():
        plan = cache.plans[plan_id]
        steps = plan['steps'].get(step, [])
        for plan_notification_id in steps:
            msg_info.append((incident_id, plan_notification_id))
    count, error_incident_ids = create_messages(msg_info)
    msg_count += count

    # Update incident step value
    for incident_id, (plan_id, step) in escalations.items():
        plan = cache.plans[plan_id]
        steps = plan['steps'].get(step, [])
        retries = 0
        max_retries = 5
        while True:
            retries += 1
            try:
                if steps:
                    if step == 1 and incident_id in error_incident_ids:
                        # no message created due to role look up failure, reset step to
                        # 0 for retry
                        step = 0
                    cursor.execute(UPDATE_INCIDENT_SQL, (step, incident_id))
                else:
                    logger.error('plan id %d has no steps, incident id %d is invalid', plan_id, incident_id)
                    cursor.execute(INVALIDATE_INCIDENT, incident_id)

                connection.commit()
            except Exception:
                logger.warning('Failed updating incident %s. (Try %s/%s)', incident_id, retries, max_retries)
                if retries < max_retries:
                    sleep(.2)
                    continue
                else:
                    raise Exception('Failed updating batch messages retries exceeded')
            else:
                break
    cursor.close()
    connection.close()

    logger.info('[*] %s new messages', msg_count)
    logger.info('[*] escalate task finished')
    metrics.set('notifications', time.time() - start_notifications)


def aggregate(now):
    # see if it's time to send the batches
    logger.info('[-] start aggregate task - queued: %s', len(messages))
    start_aggregations = time.time()
    connection = db.engine.raw_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT `id` FROM `message` WHERE active=1')
    all_actives = {r[0] for r in cursor}
    cursor.close()
    connection.close()
    for key in list(queues.keys()):
        aggregation_window = cache.plans[key[0]].get('aggregation_window')
        if aggregation_window is None:
            logger.error('No aggregation window found for plan %s', key[0])
            aggregation_window = 0
        if now - sent.get(key, 0) >= aggregation_window:
            aggregated_message_ids = queues[key]
            active_message_ids = aggregated_message_ids & all_actives
            l = len(active_message_ids)

            if l == 1:
                m = messages.pop(next(iter(active_message_ids)))
                logger.info('aggregate - %(message_id)s pushing to send queue', m)
                message_send_enqueue(m)
            elif l > 1:
                uuid = uuid4().hex
                m = messages[next(iter(active_message_ids))]
                logger.info('aggregate - %s pushing to send queue', uuid)
                m['batch_id'] = uuid

                # Cast from set to list, as sets are not msgpack serializable
                m['aggregated_ids'] = list(active_message_ids)
                message_send_enqueue(m)

                for message_id in aggregated_message_ids:
                    messages.pop(message_id, None)
                logger.info('[-] purged %s from messages %s remaining', active_message_ids, len(messages))
            del queues[key]
            sent[key] = now
    inactive_message_ids = messages.keys() - all_actives
    logger.info('[x] dropped %s inactive messages from claimed incidents, %s remain',
                len(inactive_message_ids), len(messages))

    # remove inactive message from the queue
    for message_id in inactive_message_ids:
        messages.pop(message_id, None)

    metrics.set('aggregations', time.time() - start_aggregations)
    logger.info('[*] aggregate task finished - queued: %s', len(messages))


def poll():
    # poll unsent messages
    logger.info('[-] start send task...')
    start_send = time.time()

    connection = db.engine.raw_connection()
    cursor = connection.cursor(db.dict_cursor)
    if messages:
        cursor.execute(UNSENT_MESSAGES_SQL + ' AND `message`.`id` NOT IN %s', [tuple(messages)])
    else:
        cursor.execute(UNSENT_MESSAGES_SQL)

    new_msg_count = cursor.rowcount
    queued_msg_cnt = len(messages)
    metrics.set('new_msg_count', new_msg_count)
    logger.info('%d new messages waiting in database - queued: %d', new_msg_count, queued_msg_cnt)

    for m in cursor:
        # Set dynamic target as target if applicable
        if m.get('dynamic_target') and m.get('target') is None:
            m['target'] = m['dynamic_target']
        # iris's own email response does not have context since content and
        # subject are already set
        if m.get('context'):
            context = ujson.loads(m['context'])
            # inject meta variables
            context['iris'] = {k: m[k] for k in m if k != 'context'}
            m['context'] = context
        message_queue.put(m)

    metrics.set('poll', time.time() - start_send)
    metrics.set('queue', len(messages))
    logger.info('[*] send task finished')
    cursor.close()
    connection.close()


def fetch_and_prepare_message():
    now = time.time()
    m = message_queue.get()
    message_id = m['message_id']
    plan_id = m['plan_id']
    if plan_id is None:
        message_send_enqueue(m)
        return

    plan = cache.plans[plan_id]

    # queue key
    key = (m['plan_id'], m['application'], m['priority'], m['target'])

    # should this message be aggregated?
    aggregate = False
    last_aggregation = aggregation.get(key)
    if last_aggregation:
        if now - last_aggregation > plan['aggregation_reset']:
            # it's been long enough since the last message
            # return to immediate sending mode and clear aggregations
            del aggregation[key]
            try:
                # if we have sent batches before delete the entry for last sent
                del sent[key]
            except KeyError:
                pass
        else:
            # still getting enough messages fast enough to remain in aggregation
            aggregation[key] = now
            aggregate = True

    if aggregate:
        # we are still in a previous aggregation mode
        queues.setdefault(key, set()).add(message_id)
        messages[message_id] = m
    else:
        # does this message trigger aggregation?
        window = plan_aggregate_windows.setdefault(key, defaultdict(int))

        for bucket in list(window.keys()):
            if now - bucket > plan['threshold_window']:
                del window[bucket]

        window[now] += 1

        if sum(window.values()) > plan['threshold_count']:
            # too many messages for the aggregation key - enqueue

            # add message id to aggregation queue
            queues.setdefault(key, set()).add(message_id)
            # add message id to queue for deduping
            messages[message_id] = m
            # initialize last sent tracker
            sent[key] = now
            # initialize aggregation indicator
            aggregation[key] = now
            # TODO: also render message content here?
            audit_msg = 'Aggregated with key (%s, %s, %s, %s)' % key
            spawn(auditlog.message_change, m['message_id'], auditlog.SENT_CHANGE, '', '', audit_msg)
        else:
            # cleared for immediate sending
            message_send_enqueue(m)


def send():
    logger.info('[-] start send loop...')
    while True:
        fetch_and_prepare_message()
    logger.info('[*] send loop finished...')


def set_target_fallback_mode(message):
    try:
        connection = db.engine.raw_connection()
        cursor = connection.cursor()
        cursor.execute('''SELECT `destination`, `mode`.`name`, `mode`.`id`
                          FROM `target`
                          JOIN `target_contact` ON `target_contact`.`target_id` = `target`.`id`
                          JOIN `mode` ON `mode`.`id` = `target_contact`.`mode_id`
                          WHERE `target`.`name` = %s AND `mode`.`name` = %s''',
                       (message['target'], target_fallback_mode))
        [(destination, mode, mode_id)] = cursor
        cursor.close()
        connection.close()

        old_mode = message.get('mode', '')
        message['destination'] = destination
        message['mode'] = mode
        message['mode_id'] = mode_id
        update_message_mode(message)
        message_id = message.get('message_id')
        if message_id:
            auditlog.message_change(
                message_id, auditlog.MODE_CHANGE, old_mode, message['mode'],
                'Changing mode due to original mode failure')
        return True
    # target doesn't have email either - bail
    except ValueError:
        logger.exception('target does not have mode(%s) %r', target_fallback_mode, message)
        message['destination'] = message['mode'] = message['mode_id'] = None
        return False


def set_target_contact_by_priority(message):
    session = db.Session()
    result = session.execute('''
              SELECT `target_contact`.`destination` AS dest, `mode`.`name` AS mode_name, `mode`.`id` AS mode_id
              FROM `mode`
              JOIN `target` ON `target`.`name` = :target
              JOIN `target_type` ON `target_type`.`id` = `target`.`type_id`
              JOIN `application` ON `application`.`name` = :application

              -- left join because the "drop" mode isn't going to have a target_contact entry
              LEFT JOIN `target_contact` ON `target_contact`.`mode_id` = `mode`.`id` AND `target_contact`.`target_id` = `target`.`id`

              WHERE mode.id = IFNULL((
                        SELECT `target_application_mode`.`mode_id`
                        FROM `target_application_mode`
                        WHERE `target_application_mode`.`target_id` = target.id AND
                                `target_application_mode`.`application_id` = `application`.`id` AND
                                `target_application_mode`.`priority_id` = :priority_id
                    ), IFNULL(
                      -- 2. Lookup default setting for this app
                      (
                          SELECT `default_application_mode`.`mode_id`
                          FROM `default_application_mode`
                          WHERE    `default_application_mode`.`priority_id` = :priority_id AND
                                `default_application_mode`.`application_id` = `application`.`id`
                      ), IFNULL(
                        -- 3. lookup default user setting
                            (
                                SELECT `target_mode`.`mode_id`
                                FROM `target_mode`
                                WHERE `target_mode`.`target_id` = target.id AND
                                        `target_mode`.`priority_id` = :priority_id
                            ), (
                        -- 4. lookup default iris setting
                                SELECT `mode_id`
                                FROM `priority`
                                WHERE `id` = :priority_id
                            )
                        )
                   )
                )
                -- Make sure this mode is allowed for this application. Eg important apps can't drop.
                AND EXISTS (SELECT 1 FROM `application_mode`
                            WHERE `application_mode`.`mode_id` = `mode`.`id`
                            AND   `application_mode`.`application_id` = `application`.`id`)
                -- And ensure this only works for users
                AND `target_type`.`name` = 'user'
        ''', message)

    try:
        [(destination, mode, mode_id)] = result
    except ValueError:
        raise
    finally:
        session.close()

    if not destination and mode != 'drop':
        logger.error('Did not find destination for message %s and mode is not drop', message)
        return False

    message['destination'] = destination
    message['mode'] = mode
    message['mode_id'] = mode_id

    return True


def set_target_contact(message):
    # If we already have a destination set (eg incident tracking emails or literal_target notifications) no-op this
    if 'destination' in message and not message.get('multi-recipient'):
        return True

    # returns True if contact has been set (even if it has been changed to the fallback). Otherwise, returns False
    destination_query = '''
                SELECT `destination` FROM `target_contact`
                JOIN `target` ON `target`.`id` = `target_contact`.`target_id`
                JOIN `target_type` on `target_type`.`id` = `target`.`type_id`
                WHERE `target`.`name` = %(target)s
                AND `target_type`.`name` = 'user'
                AND (`target_contact`.`mode_id` = %(mode_id)s OR `target_contact`.`mode_id` = (SELECT `id` FROM `mode` WHERE `name` = %(mode)s))
                LIMIT 1'''

    # Handle multi-recipient messages. These are only allowed when mode is specified, not priority.
    # Return True if we're able to resolve at least one target
    if message.get('multi-recipient'):
        connection = db.engine.raw_connection()
        cursor = connection.cursor()
        for t in message['target']:
            try:
                cursor.execute(destination_query, {'target': t['target'], 'mode_id': message.get('mode_id'), 'mode': message.get('mode')})
                if t.get('bcc'):
                    message['bcc_destination'].append(cursor.fetchone()[0])
                else:
                    message['destination'].append(cursor.fetchone()[0])
            except (ValueError, TypeError):
                continue
        cursor.close()
        connection.close()
        return bool(message.get('destination') or message.get('bcc_destination'))

    try:
        if 'mode' in message or 'mode_id' in message:
            # for out of band notification, we already have the mode *OR*
            # mode_id set by API
            connection = db.engine.raw_connection()
            cursor = connection.cursor()
            cursor.execute(destination_query, {'target': message['target'], 'mode_id': message.get('mode_id'), 'mode': message.get('mode')})
            message['destination'] = cursor.fetchone()[0]
            cursor.close()
            connection.close()
            result = True
        elif 'category' in message:
            connection = db.engine.raw_connection()
            cursor = connection.cursor()
            cursor.execute('''
                SELECT `mode`.`id`, `mode`.`name` FROM `category_override`
                JOIN `target` ON `target`.`id` = `category_override`.`user_id`
                JOIN `mode` ON `mode`.`id` = `category_override`.`mode_id`
                WHERE `target`.`name` = %(target)s AND `category_override`.`category_id` = %(category_id)s
            ''', {'target': message['target'], 'category_id': message['category_id']})
            override_mode = cursor.fetchone()
            if override_mode:
                message['mode_id'] = override_mode[0]
                message['mode'] = override_mode[1]
            else:
                message['mode_id'] = message['category_mode_id']
                message['mode'] = message['category_mode']
            cursor.execute('''
                SELECT `destination` FROM `target_contact`
                JOIN `target` ON `target`.`id` = `target_contact`.`target_id`
                JOIN `target_type` on `target_type`.`id` = `target`.`type_id`
                WHERE `target`.`name` = %(target)s
                AND `target_type`.`name` = 'user'
                AND `target_contact`.`mode_id` = %(mode_id)s
                LIMIT 1
                ''', {'target': message['target'], 'mode_id': message['mode_id']})
            message['destination'] = cursor.fetchone()[0]
            cursor.close()
            connection.close()
            result = True
        else:
            # message triggered by incident will only have priority
            result = set_target_contact_by_priority(message)
        if result:
            cache.target_reprioritization(message)
        else:
            logger.warning('target does not have mode %r', message)
            result = set_target_fallback_mode(message)
        return result
    except (ValueError, TypeError):
        logger.exception('target does not have mode %r', message)
        return set_target_fallback_mode(message)


def render(message):
    if not message.get('template'):
        if message.get('message_id'):
            # email response from iris does not use template this means the
            # message content is already in DB
            connection = db.engine.raw_connection()
            cursor = connection.cursor()
            cursor.execute('SELECT `body`, `subject` FROM `message` WHERE `id` = %s',
                           message['message_id'])
            msg_content = cursor.fetchone()
            message['body'], message['subject'] = msg_content[0], msg_content[1]
            cursor.close()
            connection.close()
        else:
            # out of band message does not have id and should already have the
            # content populated
            return
    elif 'aggregated_ids' in message:
        message['subject'] = '[%%(application)s] %s messages from plan %%(plan)s' % len(message['aggregated_ids']) % message
        message['body'] = 'Batch ID: %(batch_id)s' % message
        message['template_id'] = None
    else:
        if message.get('body') is None:
            message['body'] = ''
        error = None
        try:
            template = cache.templates[message['template']]
            try:
                application_template = template[message['application']]
                try:
                    # When we want to "render" a dropped message, treat it as if it's an email
                    mode_template = application_template['email' if message['mode'] == 'drop' else message['mode']]
                    try:
                        message['subject'] = mode_template['subject'].render(**message['context'])
                    except Exception as e:
                        error = 'template %(template)s - %(application)s - %(mode)s - subject failed to render: ' + str(e)
                    try:
                        message['body'] += mode_template['body'].render(**message['context'])
                    except Exception as e:
                        error = 'template %(template)s - %(application)s - %(mode)s - body failed to render: ' + str(e)
                    message['template_id'] = template['id']
                except KeyError:
                    error = 'template %(template)s - %(application)s does not have mode %(mode)s'
            except KeyError:
                error = 'template %(template)s does not have application %(application)s'
        except KeyError:
            error = 'template %(template)s does not exist'

        if error:
            # TODO:
            # define application default template here
            # additionally, instead of repr() as the final message render
            # format define a generic template that will work for all contexts
            # - even those that are invalid as a final final format maybe repr or pprint
            logger.error(error, message)
            message['subject'] = '%(message_id)s Iris failed to render your message' % message
            message['body'] = 'Failed rendering message.\n\nContext: %s\n\nError: %s' % (repr(message), error % message)
            message['template_id'] = None
        else:
            if config.get('enable_gmail_oneclick') and message['mode'] == 'email' and 'incident_id' in message:
                oneclick_url = generate_oneclick_url(config, {
                    'msg_id': message['message_id'],
                    'email_address': message['destination'],
                    'cmd': 'claim'
                })
                additional_body = oneclick_email_markup % {
                    'url': oneclick_url,
                    'incident_id': message['incident_id']
                }
                message['extra_html'] = additional_body


def mark_message_as_sent(message):
    connection = db.engine.raw_connection()

    params = [
        message['destination'],
        message['mode_id'],
        message.get('template_id'),
    ]

    if 'aggregated_ids' in message:
        sql = SENT_MESSAGE_BATCH_SQL % connection.escape(message['aggregated_ids'])
        params.append(message['batch_id'])
        message_ids = message['aggregated_ids']
    else:
        sql = SENT_MESSAGE_SQL
        params.append(message['message_id'])
        message_ids = [message['message_id']]

    cursor = connection.cursor()
    if not message['subject']:
        message['subject'] = ''
        logger.warning('Message id %s has blank subject', message.get('message_id', '?'))

    max_retries = 3

    # this deadlocks sometimes. try until it doesn't.
    for i in range(1, max_retries + 1):
        try:
            cursor.execute(sql, params)
            connection.commit()
            break
        except DataError:
            logger.warning('Failed updating message metadata status (message ID %s) (application %s)', message.get('message_id', '?'), message.get('application', '?'))
            break
        except Exception:
            if i == max_retries:
                logger.warning('Failed running sent message update query. (Try %s/%s)', i, max_retries)
            else:
                logger.warning('Failed running sent message update query. (Try %s/%s)', i, max_retries)
            sleep(.2)

    # Clean messages cache
    for message_id in message_ids:
        messages.pop(message_id, None)

    # Update subject and body separately, as they may fail and we don't necessarily care if they do
    if len(message['subject']) > 255:
        message['subject'] = message['subject'][:255]

    if len(message['body']) > MAX_MESSAGE_BODY_LENGTH:
        logger.warning('Message id %s has a ridiculously long body (%s chars). Truncating it.',
                       message.get('message_id', '?'), len(message['body']))
        message['body'] = message['body'][:MAX_MESSAGE_BODY_LENGTH]

    if 'aggregated_ids' in message:
        update_ids = tuple(message['aggregated_ids'])
    else:
        update_ids = tuple([message['message_id']])

    max_retries = 3

    # this deadlocks sometimes. try until it doesn't.
    for i in range(1, max_retries + 1):
        try:
            cursor.execute(UPDATE_MESSAGE_BODY_SQL, (message['body'], message['subject'], update_ids))
            connection.commit()
            break
        except DataError:
            logger.warning('Failed updating message body+subject (message IDs %s) (application %s)', update_ids, message.get('application', '?'))
            break
        except Exception:
            if i == max_retries:
                logger.warning('Failed updating message body+subject (message IDs %s) (application %s) (Try %s/%s)', update_ids, message.get('application', '?'), i, max_retries)
            else:
                logger.warning('Failed updating message body+subject (message IDs %s) (application %s) (Try %s/%s)', update_ids, message.get('application', '?'), i, max_retries)
            sleep(.2)

    cursor.close()
    connection.close()


def update_message_sent_status(message, status):
    message_id = message.get('message_id')
    if not message_id:
        return

    mode = message.get('mode')

    if not mode:
        return

    # Don't track this for twilio as those are kept track of separately. Make
    # use of this for email, and, as a side effect of that for slack
    if mode in ('sms', 'call'):
        return

    session = db.Session()
    retries = 0
    max_retries = 3
    while True:
        retries += 1
        try:
            session.execute('''INSERT INTO `generic_message_sent_status` (`message_id`, `status`)
                        VALUES (:message_id, :status)
                        ON DUPLICATE KEY UPDATE `status` =  :status''',
                            {'message_id': message_id, 'status': status})
            session.commit()
        except Exception:
            logger.warning('Failed setting message sent status for message %s (Try %s/%s)', message_id, retries, max_retries)
            if retries < max_retries:
                sleep(.2)
                continue
            else:
                raise Exception('Failed setting message sent status for message retries exceeded')
        else:
            break

    session.close()


def mark_message_has_no_contact(message):
    message_id = message.get('message_id')
    if not message_id:
        logger.warning('Cannot mark message "%s" as not having contact as message_id is missing', message)
        return

    connection = db.engine.raw_connection()
    cursor = connection.cursor()
    retries = 0
    max_retries = 3
    while True:
        retries += 1
        try:
            cursor.execute('UPDATE `message` set `active`=0 WHERE `id`=%s',
                           message_id)
            connection.commit()
            cursor.close()
        except Exception:
            logger.warning('Failed setting message %s as not having contact (Try %s/%s)', message_id, retries, max_retries)
            if retries < max_retries:
                sleep(.2)
                continue
            else:
                raise Exception('Failed setting message as not having contact')
        else:
            break
    connection.close()
    auditlog.message_change(
        message_id, auditlog.MODE_CHANGE, target_fallback_mode, 'invalid',
        'Ignore message as we failed to resolve target contact')


def distributed_send_message(message, vendor_manager):
    # If I am the master and this message isn't for a slave, attempt
    # sending my messages through my slaves.
    if not message.get('to_slave') and coordinator.am_i_master():
        try:
            if coordinator.slave_count and coordinator.slaves:
                for i, address in enumerate(coordinator.slaves):
                    if i >= coordinator.slave_count:
                        logger.error('Failed using all configured slaves; resorting to local send_message')
                        break
                    if rpc.send_message_to_slave(message, address):
                        return True, False
        except StopIteration:
            logger.warning('No more slaves. Sending locally.')

    logger.info('Sending message (ID %s) locally', message.get('message_id', '?'))

    runtime = vendor_manager.send_message(message)
    add_mode_stat(message['mode'], runtime)

    # application is not present for incident tracking emails
    if 'application' in message:
        notification_count = 1 if not message.get('target_list') else len(message['destination'])
        metrics_key = 'app_%(application)s_mode_%(mode)s_cnt' % message
        metrics.add_new_metrics({metrics_key: 0})
        metrics.incr(metrics_key, inc=notification_count)

    if runtime is not None:
        return True, True

    return False, False


def fetch_and_send_message(send_queue, vendor_manager):
    try:
        message = send_queue.get(True, 4)
    except queue.Empty:
        return

    metrics.incr('send_queue_gets_cnt')

    retry_count = message.get('retry_count')
    is_retry = retry_count is not None
    if is_retry and retry_count >= MAX_MESSAGE_RETRIES:
        logger.warning('Maximum retry count for app: %s target:%s breached', message.get('application', '?'), message.get('target', '?'))
        return

    if not is_retry:
        sanitize_unicode_dict(message)

    if 'message_id' not in message:
        message['message_id'] = None

    message_to_slave = message.get('to_slave', False)

    drop_mode_id = api_cache.modes.get('drop')

    # If this app breaches hard quota, drop message on floor, and update in UI if it has an ID
    if not is_retry and not message_to_slave and not quota.allow_send(message):
        logger.warning('Hard message quota exceeded; Dropping this message on floor: %s', message)
        if message['message_id']:
            spawn(auditlog.message_change,
                  message['message_id'], auditlog.MODE_CHANGE, message.get('mode', '?'), 'drop',
                  'Dropping due to hard quota violation.')

            # If we know the ID for the mode drop, reflect that for the message
            if drop_mode_id:
                message['mode'] = 'drop'
                message['mode_id'] = drop_mode_id
            else:
                logger.error('Can\'t mark message %s as dropped as we don\'t know the mode ID for %s',
                             message, 'drop')

            # Render, so we're able to populate the message table with the
            # proper subject/etc as well as information that it was dropped.
            render(message)
            mark_message_as_sent(message)
        return

    # If we're set to drop this message, no-op this before message gets sent to a vendor
    if message.get('mode') == 'drop':
        if message['message_id']:
            render(message)
            mark_message_as_sent(message)
        add_mode_stat('drop', 0)

        metrics_key = 'app_%(application)s_mode_drop_cnt' % message
        metrics.add_new_metrics({metrics_key: 0})
        metrics.incr(metrics_key)

        return

    # Only render this message and validate its body/etc if it's not a retry, in which case this
    # step would have been done before
    if not is_retry and not message_to_slave:
        render(message)

        if message.get('body') is None:
            message['body'] = ''

        # Drop this message, and mark it as dropped, rather than sending it, if its
        # body is too long and we were normally going to send it anyway.
        body_length = len(message['body'])
        if body_length > MAX_MESSAGE_BODY_LENGTH:
            logger.warning('Message id %s has a ridiculously long body (%s chars). Dropping it.',
                           message['message_id'], body_length)
            spawn(auditlog.message_change,
                  message['message_id'], auditlog.MODE_CHANGE, message.get('mode', '?'), 'drop',
                  'Dropping due to excessive body length (%s > %s chars)' % (
                      body_length, MAX_MESSAGE_BODY_LENGTH))

            metrics.incr('msg_drop_length_cnt')

            # Truncate this here to avoid a duplicate log message in
            # mark_message_as_sent(), as we still need to call that to update the body/subject
            message['body'] = message['body'][:MAX_MESSAGE_BODY_LENGTH]

            if drop_mode_id:
                message['mode'] = 'drop'
                message['mode_id'] = drop_mode_id

            mark_message_as_sent(message)
            return

    success = False
    sent_locally = False
    try:
        success, sent_locally = distributed_send_message(message, vendor_manager)
    except Exception:
        logger.warning('Failed to send message: %s', message)
        add_mode_stat(message['mode'], None)
    if not success and not sent_locally:
        if not message.get('unexpanded') and message['mode'] != 'email':
            if message.get('target'):
                logger.error('reclassifying as email %s', message)
                set_target_fallback_mode(message)
                render(message)
                try:
                    success, sent_locally = distributed_send_message(message, vendor_manager)
                # nope - log and bail
                except Exception:
                    metrics.incr('task_failure')
                    add_mode_stat(message['mode'], None)
                    logger.error('unable to send %s', message)
                    sent_locally = True

    # Take it out of our list of active queued messages if it's there
    if message['message_id']:
        message_ids_being_sent.discard(message['message_id'])

    if success:
        metrics.incr('message_send_cnt')
        if message['message_id'] and sent_locally:
            mark_message_as_sent(message)

        if message_to_slave:
            metrics.incr('slave_message_send_success_cnt')

    else:
        # If we're not successful, try retrying it
        message['retry_count'] = message.get('retry_count', 0) + 1
        message_send_enqueue(message)
        metrics.incr('message_retry_cnt')
        logger.info('Message %s failed. Re-queuing for retry (%s/%s).', message, message['retry_count'], MAX_MESSAGE_RETRIES)

        if message_to_slave:
            metrics.incr('slave_message_send_fail_cnt')

    if message['message_id'] and sent_locally:
        update_message_sent_status(message, success)


def worker(send_queue, worker_config, kill_set):
    vendor_manager = IrisVendorManager(worker_config.get('vendors', []), worker_config.get('applications', []))
    while True:
        fetch_and_send_message(send_queue, vendor_manager)

        if kill_set.is_set():
            vendor_manager.cleanup()
            return


def maintain_workers(config):
    # We mangle this config dict a bit and pass it around. Avoid latering the main one
    config = copy.deepcopy(config)

    # Determine counts for "normal" modes
    default_worker_count = 100

    try:
        worker_count = int(config.get('sender_workers', default_worker_count))
    except ValueError:
        worker_count = default_worker_count

    workers_per_mode_cnt = worker_count // len(api_cache.modes)
    workers_per_mode = {mode: workers_per_mode_cnt for mode in api_cache.modes}

    # Email scale up/down. For this trickyness to work: 1) Only one SMTP vendor 2) It has "autoscale" enabled
    # 3) It uses SMTP gateway instead of hard coded mx_servers

    email_vendor = None
    email_mx_gateway = None
    email_smtp_workers = None
    configured_vendors = config['vendors']
    for vendor in configured_vendors:
        if vendor['type'] == 'iris_smtp':
            email_mx_gateway = vendor.get('smtp_gateway')
            if not email_mx_gateway:
                break

            if not vendor.get('autoscale'):
                logger.warning('Ignoring possibly auto scaled MX gateway %s', email_mx_gateway)
                break

            email_vendor = vendor
            break

    # Hard code workers for each mode manually in config
    workers_per_mode_config = config.get('sender', {}).get('workers_per_mode', {})
    workers_per_mode.update({mode: int(workers_per_mode_config[mode]) for mode in api_cache.modes if mode in workers_per_mode_config})

    email_autoscale = email_vendor is not None

    if email_autoscale:
        try:
            email_smtp_workers = iris_smtp.iris_smtp.determine_worker_count(email_vendor)
        except Exception:
            logger.warning('Failed determining MX records this round')
            email_smtp_workers = None

        old_email_worker_count = workers_per_mode.pop('email', None)
        if old_email_worker_count:
            logger.info('Going with autoscaled smtp workers instead of %d', old_email_worker_count)

        # Remove all smtp vendor objects so they don't get initialized unnecessarily
        config['vendors'] = [vendor for vendor in config['vendors'] if vendor['type'] != 'iris_smtp']

    logger.info('Workers per mode: %s', ', '.join('%s: %s' % count for count in iter(workers_per_mode.items())))

    # Make sure all the counts and distributions for "normal" workers are proper, including email if we're not doing MX record
    # autoscaling

    for mode, worker_count in workers_per_mode.items():
        mode_tasks = worker_tasks[mode]
        if mode_tasks:
            for task in mode_tasks:
                if not bool(task['greenlet']):
                    logger.error("worker task for mode %s failed, %s. Respawning", mode, task['greenlet'].exception)
                    kill_set = gevent.event.Event()
                    task.update({'greenlet': spawn(worker, per_mode_send_queues[mode], config, kill_set), 'kill_set': kill_set})
                    metrics.incr('workers_respawn_cnt')
        else:
            for x in range(worker_count):
                kill_set = gevent.event.Event()
                mode_tasks.append({'greenlet': spawn(worker, per_mode_send_queues[mode], config, kill_set), 'kill_set': kill_set})

    # Maintain, grow, and shrink email workers
    if email_autoscale and email_smtp_workers:
        logger.info('Configuring auto scaling smtp records')
        email_queue = per_mode_send_queues['email']
        tasks_to_kill = []

        # Adjust worker count
        for mx, correct_worker_count in email_smtp_workers.items():
            mx_workers = autoscale_email_worker_tasks[mx]
            current_task_count = len(mx_workers)

            # Correct amount of workers
            if current_task_count == correct_worker_count:
                logger.info('MX record %s has the correct number of tasks %d', mx, correct_worker_count)

            # Need more workers
            elif current_task_count < correct_worker_count:
                new_task_count = correct_worker_count - current_task_count
                logger.info('Auto scaling MX record %s UP %d tasks', mx, new_task_count)

                # Configure this email worker with just one hard coded mx server, the one this
                # worker will correspond to
                email_vendor_config = copy.deepcopy(email_vendor)
                email_vendor_config['smtp_server'] = mx
                email_vendor_config.pop('smtp_gateway', None)
                worker_config = copy.deepcopy(config)
                worker_config['vendors'] = [email_vendor_config]

                for x in range(new_task_count):
                    kill_set = gevent.event.Event()
                    mx_workers.append({'greenlet': spawn(worker, email_queue, worker_config, kill_set), 'kill_set': kill_set})

            # Need less workers
            elif current_task_count > correct_worker_count:
                kill_task_count = current_task_count - correct_worker_count
                logger.info('Auto scaling MX record %s DOWN %d tasks', mx, kill_task_count)
                for x in range(kill_task_count):
                    try:
                        tasks_to_kill.append(mx_workers.pop())
                    except IndexError:
                        break

        # Kill MX records no longer in use
        kill_mx = autoscale_email_worker_tasks.keys() - email_smtp_workers.keys()
        for mx in kill_mx:
            workers = autoscale_email_worker_tasks[mx]
            if workers:
                logger.info('Removing %d tasks for unused MX %s', len(workers), mx)
                tasks_to_kill += workers
            del autoscale_email_worker_tasks[mx]

        # Make sure all existing workers are alive
        for mx, mx_tasks in autoscale_email_worker_tasks.items():
            email_vendor_config = copy.deepcopy(email_vendor)
            email_vendor_config['smtp_server'] = mx
            email_vendor_config.pop('smtp_gateway', None)
            worker_config = copy.deepcopy(config)
            worker_config['vendors'] = [email_vendor_config]

            for task in mx_tasks:
                if not bool(task['greenlet']):
                    kill_set = gevent.event.Event()
                    task.update({'greenlet': spawn(worker, email_queue, worker_config, kill_set), 'kill_set': kill_set})
                    logger.error("worker email task for mx %s failed, %s. Respawning", mx, task['greenlet'].exception)
                    metrics.incr('workers_respawn_cnt')

        # Kill all of the workers who shouldn't exist anymore
        for task in tasks_to_kill:
            task['kill_set'].set()


def gwatch_renewer():
    gmail_config = config['gmail']
    gcli = Gmail(gmail_config, config.get('gmail_proxy'))
    while True:
        # If we stop being master, bail out of this
        if coordinator is not None and not coordinator.am_i_master():
            return

        logger.info('[-] start gmail watcher loop...')
        logger.info('renewing gmail watcher...')
        re = gcli.watch(gmail_config['project'], gmail_config['topic'])
        try:
            history_id, expiration = (int(re['historyId']),
                                      int(re['expiration']) / 1000 - time.time())
        except KeyError:
            logger.exception('[*] gmail watcher run failed. Skipping this run.')
        else:
            metrics.set('gmail_history_id', history_id)
            metrics.set('gmail_seconds_to_watch_expiration', expiration)
            logger.info('[*] gmail watcher loop finished')

        # only renew every 8 hours
        sleep(60 * 60 * 8)


def prune_old_audit_logs_worker():
    while True:
        # If we stop being master, bail out of this
        if coordinator is not None and not coordinator.am_i_master():
            return

        try:
            connection = db.engine.raw_connection()
            cursor = connection.cursor()
            cursor.execute(PRUNE_OLD_AUDIT_LOGS_SQL)
            connection.commit()
            cursor.close()
        except Exception:
            logger.warning('Failed pruning old audit logs')
        finally:
            connection.close()

        logger.info('Ran task to prune old audit logs. Waiting 4 hours until next run.')
        sleep(60 * 60 * 4)


def mock_gwatch_renewer():
    while True:
        logger.info('[-] start mock gmail watcher loop...')
        logger.info('[*] mock gmail watcher loop finished')
        sleep(60)


def sender_shutdown():
    global shutdown_started

    # Make control+c or some other kill signal force quit the second time it happens
    if shutdown_started:
        logger.info('Force exiting')
        os._exit(0)
    else:
        shutdown_started = True
        logger.info('Shutting server..')

    # Immediately release all locks and give up any master status and slave presence
    if coordinator:
        coordinator.leave_cluster()

    # Stop sender RPC server
    rpc.shutdown()

    for tasks in worker_tasks.values():
        for task in tasks:
            task['kill_set'].set()

    for tasks in autoscale_email_worker_tasks.values():
        for task in tasks:
            task['kill_set'].set()

    logger.info('Waiting for sender workers to shut down')

    for tasks in worker_tasks.values():
        for task in tasks:
            task['greenlet'].join()

    for tasks in autoscale_email_worker_tasks.values():
        for task in tasks:
            task['greenlet'].join()

    # Force quit. Avoid sender process existing longer than it needs to
    os._exit(0)


def modify_restricted_calls(message):
    # check for known corner cases in message delivery and correct accordingly

    # due to calling restrictions to china override mode and send as sms instead
    if message['destination'].startswith('+86'):
        message['mode'] = 'sms'
        auditlog.message_change(
            message['message_id'], auditlog.MODE_CHANGE, 'call', 'sms',
            'Changing mode due to calling restriction')
        # this message will appear before the contents of the sms template
        message['body'] = 'Due to legal restrictions we are unable to deliver calls to China. Please check Iris for complete incident details and change your settings to use sms, slack, or email instead - ' + message.get('body', '')


def modify_restricted_sms(message):

    if message.get('incident_id'):
        # Alter message to get around SMS restrictions in countries like India
        # Replace body with pre-registered template so it won't be dropped by carriers

        destination = message['destination']
        message_id = message['message_id']
        mode_id = message['mode_id']
        connection = db.engine.raw_connection()
        cursor = connection.cursor()
        # only replace messages for users that have opted in
        cursor.execute('''SELECT count(`mode_template_override`.`target_id`)
            FROM `mode_template_override` JOIN `target_contact`
            ON `mode_template_override`.`target_id` = `target_contact`.`target_id`
            WHERE `target_contact`.`destination` = %s and `target_contact`.`mode_id` = %s''', (destination, mode_id))
        result = cursor.fetchone()[0]
        connection.close()
        if result:
            body_template = config.get('sms_override_template')
            message['body'] = body_template % message.get('incident_id')
            auditlog.message_change(message_id, auditlog.CONTENT_CHANGE, 'sms', 'sms',
                                    'Replaced SMS body to avoid being blocked by carrier')


def message_send_enqueue(message):

    # If this message has an ID, avoid queueing it twice, assuming it's not a retry
    message_id = message.get('message_id')
    if message_id is not None and message_id in message_ids_being_sent and not message.get('retry_count'):
        logger.debug('Not-requeueing message %s', message)
        return

    # Set the target contact here so we determine the mode, which determines the
    # queue it gets inserted into. Skip this step if it's a retry because we'd
    # already have the message's contact info decided
    if not message.get('retry_count'):
        has_contact = set_target_contact(message)
        if not has_contact:
            mark_message_has_no_contact(message)
            metrics.incr('task_failure')
            logger.error('Failed to send message, no contact found: %s', message)
            return

    message_mode = message.get('mode')
    if message_mode and message_mode in per_mode_send_queues:
        # check for known corner case limitations and correct accordingly
        if message['mode'] == 'call':
            modify_restricted_calls(message)

        if message['mode'] == 'sms':
            modify_restricted_sms(message)

        if message_id is not None:
            message_ids_being_sent.add(message_id)
        per_mode_send_queues[message_mode].put(message)
        metrics.incr('send_queue_puts_cnt')
    else:
        logger.error('Message %s does not have proper mode %s', message, message_mode)
        metrics.incr('send_queue_puts_fail_cnt')


def update_api_cache_worker():
    while True:
        logger.debug('Reinitializing cache')
        api_cache.cache_priorities()
        api_cache.cache_applications()
        api_cache.cache_modes()
        sleep(60)


def init_sender(config):
    gevent.signal(signal.SIGINT, sender_shutdown)
    gevent.signal(signal.SIGTERM, sender_shutdown)
    gevent.signal(signal.SIGQUIT, sender_shutdown)

    process_title = config['sender'].get('process_title')

    if process_title and isinstance(process_title, str):
        setproctitle.setproctitle(process_title)
        logger.info('Changing process name to %s', process_title)

    api_host = config['sender'].get('api_host', 'http://localhost:16649')
    db.init(config)
    cache.init(api_host, config)
    metrics.init(config, 'iris-sender', default_sender_metrics)
    api_cache.cache_priorities()
    api_cache.cache_applications()
    api_cache.cache_modes()

    global should_mock_gwatch_renewer, send_message
    if config['sender'].get('debug'):
        logger.info('DEBUG MODE')
        should_mock_gwatch_renewer = True
        should_skip_send = True
    else:
        should_skip_send = False
    should_mock_gwatch_renewer = should_mock_gwatch_renewer or config.get('skipgmailwatch', False)
    should_skip_send = should_skip_send or config.get('skipsend', False)

    if should_skip_send:
        config['vendors'] = [{
            'type': 'iris_dummy',
            'name': 'iris dummy vendor'
        }]

    global quota
    quota = ApplicationQuota(db, cache.targets_for_role, message_send_enqueue, config['sender'].get('sender_app'))

    global coordinator
    zk_hosts = config['sender'].get('zookeeper_cluster', False)

    if zk_hosts:
        logger.info('Initializing coordinator with ZK: %s', zk_hosts)
        from iris.coordinator.kazoo import Coordinator
        coordinator = Coordinator(zk_hosts=zk_hosts,
                                  hostname=socket.gethostname(),
                                  port=config['sender'].get('port', 2321),
                                  join_cluster=True)
    else:
        logger.info('ZK cluster info not specified. Using master status from config')
        from iris.coordinator.noncluster import Coordinator
        coordinator = Coordinator(is_master=config['sender'].get('is_master', True),
                                  slaves=config['sender'].get('slaves', []))


def main():
    global config
    global shutdown_started
    config = load_config()

    start_time = time.time()

    logger.info('[-] bootstraping sender...')
    init_sender(config)
    spawn(update_api_cache_worker)
    init_plugins(config.get('plugins', {}))

    if not rpc.run(config['sender']):
        sender_shutdown()

    for mode in api_cache.modes:
        per_mode_send_queues[mode] = queue.Queue()

    rpc.init(config['sender'], dict(
        message_send_enqueue=message_send_enqueue
    ))

    spawn(coordinator.update_forever)
    send_task = spawn(send)

    maintain_workers(config)

    disable_gwatch_renewer = config['sender'].get('disable_gwatch_renewer', False)
    gwatch_renewer_task = None
    prune_audit_logs_task = None

    interval = 60
    logger.info('[*] sender bootstrapped')
    while True:

        # When the shutdown starts, avoid doing sender tasks but keep this
        # loop open as the shutdown function terminates the app once messages
        # are done sending.
        if shutdown_started:
            logger.info('--> Shutdown in progress')
            sleep(30)
            continue

        runtime = int(time.time())
        logger.info('--> sender looop started.')

        cache.refresh()
        cache.purge()

        # If we're currently a master, ensure our master-greenlets are running
        # and we're doing the master duties
        if coordinator.am_i_master():
            if not disable_gwatch_renewer and not bool(gwatch_renewer_task):
                if should_mock_gwatch_renewer:
                    gwatch_renewer_task = spawn(mock_gwatch_renewer)
                else:
                    gwatch_renewer_task = spawn(gwatch_renewer)

            if not bool(prune_audit_logs_task):
                prune_audit_logs_task = spawn(prune_old_audit_logs_worker)

            try:
                escalate()
                deactivate()
                poll()
                aggregate(runtime)
            except Exception:
                metrics.incr('task_failure')
                logger.exception("Exception occured in main loop.")

        # If we're not master, don't do the master tasks and make sure those other
        # greenlets are stopped if they're running
        else:
            logger.info('I am not the master so I am not doing master sender tasks.')

            # Stop these task greenlets if they're running. Technically this should
            # never happen because if we're the master, we'll likely only stop being the
            # master if our process exits, which would kill these greenlets anyway.
            if bool(gwatch_renewer_task):
                logger.info('I am not master anymore so stopping the gwatch renewer')
                gwatch_renewer_task.kill()

            if bool(prune_audit_logs_task):
                logger.info('I am not master anymore so stopping the audit logs worker')
                prune_audit_logs_task.kill()

        # check status for all background greenlets and respawn if necessary
        if not bool(send_task):
            logger.error("send task failed, %s", send_task.exception)
            metrics.incr('task_failure')
            send_task = spawn(send)

        for mode, send_queue in per_mode_send_queues.items():

            # Set metric for size of worker queue
            metrics.set('send_queue_%s_size' % mode, len(send_queue))

        maintain_workers(config)

        now = time.time()
        metrics.set('sender_uptime', int(now - start_time))

        metrics.set('message_ids_being_sent_cnt', len(message_ids_being_sent))

        spawn(metrics.emit)

        elapsed_time = now - runtime
        nap_time = max(0, interval - elapsed_time)
        logger.info('--> sender loop finished in %s seconds - sleeping %s seconds',
                    elapsed_time, nap_time)
        sleep(nap_time)


if __name__ == '__main__':
    main()
