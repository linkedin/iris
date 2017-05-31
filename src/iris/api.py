# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from __future__ import absolute_import

from gevent import socket
import msgpack
import time
import hmac
import hashlib
import base64
import re
import os
import datetime
import logging
import jinja2
from jinja2.sandbox import SandboxedEnvironment
from urlparse import parse_qs
import ujson
from falcon import HTTP_200, HTTP_201, HTTP_204, HTTPBadRequest, HTTPNotFound, HTTPUnauthorized, HTTPForbidden, HTTPFound, API
from falcon_cors import CORS
from sqlalchemy.exc import IntegrityError
import falcon.uri

from collections import defaultdict
from streql import equals

from . import db
from . import utils
from . import cache
from . import ui
from .config import load_config
from iris.sender import auditlog
from iris.sender.quota import (get_application_quotas_query, insert_application_quota_query,
                               required_quota_keys, quota_int_keys)

from gevent import spawn, sleep


from .constants import (
    XFRAME, XCONTENTTYPEOPTIONS, XXSSPROTECTION
)

from .plugins import init_plugins, find_plugin
from .validators import init_validators, run_validation, IrisValidationException

logger = logging.getLogger(__name__)

operators = {
    '': '%s = %s',
    'eq': '%s = %s',
    'in': '%s in %s',
    'ne': '%s != %s',
    'gt': '%s > %s',
    'ge': '%s >= %s',
    'lt': '%s < %s',
    'le': '%s <= %s',
    'contains': '%s LIKE CONCAT("%%%%", %s, "%%%%")',
    'startswith': '%s LIKE CONCAT(%s, "%%%%")',
    'endswith': '%s LIKE CONCAT("%%%%", %s)',
}


def ts_to_sql_datetime(ts):
    return 'FROM_UNIXTIME(%s)' % ts


filter_escaped_value_transforms = {
    'updated': ts_to_sql_datetime,
    'created': ts_to_sql_datetime,
    'sent': ts_to_sql_datetime,
}

message_columns = {
    'id': '`message`.`id` as `id`',
    'active': '`message`.`active` as `active`',
    'batch': '`message`.`batch` as `batch`',
    'created': 'UNIX_TIMESTAMP(`message`.`created`) as `created`',
    'sent': 'UNIX_TIMESTAMP(`message`.`sent`) as `sent`',
    'destination': '`message`.`destination` as `destination`',
    'subject': '`message`.`subject` as `subject`',
    'incident_id': '`message`.`incident_id` as `incident_id`',
    'mode': '`mode`.`name` as `mode`',
    'application': '`application`.`name` as `application`',
    'priority': '`priority`.`name` as `priority`',
    'target': '`target`.`name` as `target`',
    'body': '`message`.`body` as `body`',
    'mode_changed': 'exists(SELECT 1 FROM `message_changelog` WHERE `message_id` = `message`.`id` AND `change_type` = %(mode_change)s) as mode_changed',
    'target_changed': 'exists(SELECT 1 FROM `message_changelog` WHERE `message_id` = `message`.`id` AND `change_type` = %(target_change)s) as target_changed'
}

message_filters = {
    'id': '`message`.`id`',
    'active': '`message`.`active`',
    'batch': '`message`.`batch`',
    'created': '`message`.`created`',
    'sent': '`message`.`sent`',
    'destination': '`message`.`destination`',
    'subject': '`message`.`subject`',
    'incident_id': '`message`.`incident_id`',
    'mode': '`mode`.`name`',
    'application': '`application`.`name`',
    'priority': '`priority`.`name`',
    'target': '`target`.`name`',
    'body': '`message`.`body`',
}


message_filter_types = {
    'id': int,
    'created': int,
    'sent': int,
}

message_query = '''SELECT %s FROM `message`
 JOIN `priority` ON `message`.`priority_id` = `priority`.`id`
 JOIN `application` ON `message`.`application_id` = `application`.`id`
 JOIN `mode` ON `message`.`mode_id` = `mode`.`id`
 JOIN `target` ON `message`.`target_id`=`target`.`id`'''

single_message_query = '''SELECT `message`.`id` as `id`,
    `message`.`active` as `active`,
    `message`.`batch` as `batch`,
    `message`.`body` as `body`,
    UNIX_TIMESTAMP(`message`.`created`) as `created`,
    UNIX_TIMESTAMP(`message`.`sent`) as `sent`,
    `message`.`destination` as `destination`,
    `message`.`subject` as `subject`,
    `message`.`incident_id` as `incident_id`,
    `mode`.`name` as `mode`,
    `application`.`name` as `application`,
    `priority`.`name` as `priority`,
    `target`.`name` as `target`,
    `twilio_delivery_status`.`status` as `twilio_delivery_status`,
    `generic_message_sent_status`.`status` as `generic_message_sent_status`
FROM `message`
JOIN `priority` ON `message`.`priority_id` = `priority`.`id`
JOIN `application` ON `message`.`application_id` = `application`.`id`
JOIN `mode` ON `message`.`mode_id` = `mode`.`id`
JOIN `target` ON `message`.`target_id`=`target`.`id`
LEFT JOIN `twilio_delivery_status` ON `twilio_delivery_status`.`message_id` = `message`.`id`
LEFT JOIN `generic_message_sent_status` ON `generic_message_sent_status`.`message_id` = `message`.`id`
WHERE `message`.`id` = %s'''

message_audit_log_query = '''SELECT `id`, `date`, `old`, `new`, `change_type`, `description`
                             FROM `message_changelog`
                             WHERE `message_id` = %s
                             ORDER BY `date` DESC'''

incident_columns = {
    'id': '`incident`.`id` as `id`',
    'plan': '`plan`.`name` as `plan`',
    'plan_id': '`incident`.`plan_id` as `plan_id`',
    'active': '`incident`.`active` as `active`',
    'updated': 'UNIX_TIMESTAMP(`incident`.`updated`) as `updated`',
    'application': '`application`.`name` as `application`',
    'context': '`incident`.`context` as `context`',
    'created': 'UNIX_TIMESTAMP(`incident`.`created`) as `created`',
    'owner': '`target`.`name` as `owner`',
    'current_step': '`incident`.`current_step` as `current_step`',
}

incident_filters = {
    'id': '`incident`.`id`',
    'plan': '`plan`.`name`',
    'plan_id': '`incident`.`plan_id`',
    'active': '`incident`.`active`',
    'updated': '`incident`.`updated`',
    'application': '`application`.`name`',
    'context': '`incident`.`context`',
    'created': '`incident`.`created`',
    'owner': '`target`.`name`',
    'current_step': '`incident`.`current_step`',
}

incident_filter_types = {
    'id': int,
    'plan_id': int,
    'updated': int,
    'created': int,
    'current_step': int,
}

incident_query = '''SELECT %s FROM `incident`
JOIN `plan` ON `incident`.`plan_id` = `plan`.`id`
LEFT OUTER JOIN `target` ON `incident`.`owner_id` = `target`.`id`
JOIN `application` ON `incident`.`application_id` = `application`.`id`'''

single_incident_query = '''SELECT `incident`.`id` as `id`,
    `incident`.`plan_id` as `plan_id`,
    `plan`.`name` as `plan`,
    UNIX_TIMESTAMP(`incident`.`created`) as `created`,
    UNIX_TIMESTAMP(`incident`.`updated`) as `updated`,
    `incident`.`context` as `context`,
    `target`.`name` as `owner`,
    `application`.`name` as `application`,
    `incident`.`current_step` as `current_step`,
    `incident`.`active` as `active`
FROM `incident`
JOIN `plan` ON `incident`.`plan_id` = `plan`.`id`
LEFT OUTER JOIN `target` ON `incident`.`owner_id` = `target`.`id`
JOIN `application` ON `incident`.`application_id` = `application`.`id`
WHERE `incident`.`id` = %s'''

single_incident_query_steps = '''SELECT `message`.`id` as `id`,
    `target`.`name` as `name`,
    `mode`.`name` as `mode`,
    `priority`.`name` as `priority`,
    UNIX_TIMESTAMP(`message`.`created`) as `created`,
    UNIX_TIMESTAMP(`message`.`sent`) as `sent`,
    `plan_notification`.`step` as `step`,
    exists(SELECT 1 FROM `message_changelog` WHERE `message_id` = `message`.`id` AND `change_type` = %s) as mode_changed,
    exists(SELECT 1 FROM `message_changelog` WHERE `message_id` = `message`.`id` AND `change_type` = %s) as target_changed
FROM `message`
JOIN `priority` ON `message`.`priority_id` = `priority`.`id`
JOIN `mode` ON `message`.`mode_id` = `mode`.`id`
JOIN `target` ON `message`.`target_id` = `target`.`id`
JOIN `plan_notification` ON `message`.`plan_notification_id` = `plan_notification`.`id`
WHERE `message`.`incident_id` = %s
ORDER BY `message`.`sent`'''

plan_columns = {
    'id': '`plan`.`id` as `id`',
    'name': '`plan`.`name` as `name`',
    'threshold_window': '`plan`.`threshold_window` as `threshold_window`',
    'threshold_count': '`plan`.`threshold_count` as `threshold_count`',
    'aggregation_window': '`plan`.`aggregation_window` as `aggregation_window`',
    'aggregation_reset': '`plan`.`aggregation_reset` as `aggregation_reset`',
    'tracking_type': '`plan`.`tracking_type` as `tracking_type`',
    'tracking_key': '`plan`.`tracking_key` as `tracking_key`',
    'tracking_template': '`plan`.`tracking_template` as `tracking_template`',
    'description': '`plan`.`description` as `description`',
    'created': 'UNIX_TIMESTAMP(`plan`.`created`) as `created`',
    'creator': '`target`.`name` as `creator`',
    'active': 'IF(`plan_active`.`plan_id` IS NULL, FALSE, TRUE) as `active`',
}

plan_filters = {
    'id': '`plan`.`id`',
    'name': '`plan`.`name`',
    'threshold_window': '`plan`.`threshold_window`',
    'threshold_count': '`plan`.`threshold_count`',
    'aggregation_window': '`plan`.`aggregation_window`',
    'aggregation_reset': '`plan`.`aggregation_reset`',
    'description': '`plan`.`description`',
    'created': '`plan`.`created`',
    'creator': '`target`.`name`',
    'active': '`plan_active`.`plan_id`',
}

plan_filter_types = {
    'id': int,
    'created': int,
    'threshold_count': int,
    'threshold_window': int,
    'aggregation_window': int,
    'aggregation_reset': int,
}

plan_query = '''SELECT %s FROM `plan` JOIN `target` ON `plan`.`user_id` = `target`.`id`
LEFT OUTER JOIN `plan_active` ON `plan`.`id` = `plan_active`.`plan_id`'''

single_plan_query = '''SELECT `plan`.`id` as `id`, `plan`.`name` as `name`,
    `plan`.`threshold_window` as `threshold_window`, `plan`.`threshold_count` as `threshold_count`,
    `plan`.`aggregation_window` as `aggregation_window`, `plan`.`aggregation_reset` as `aggregation_reset`,
    `plan`.`description` as `description`, UNIX_TIMESTAMP(`plan`.`created`) as `created`,
    `target`.`name` as `creator`, IF(`plan_active`.`plan_id` IS NULL, FALSE, TRUE) as `active`,
    `plan`.`tracking_type` as `tracking_type`, `plan`.`tracking_key` as `tracking_key`,
    `plan`.`tracking_template` as `tracking_template`
FROM `plan` JOIN `target` ON `plan`.`user_id` = `target`.`id`
LEFT OUTER JOIN `plan_active` ON `plan`.`id` = `plan_active`.`plan_id`'''

single_plan_query_steps = '''SELECT `plan_notification`.`id` as `id`,
    `plan_notification`.`step` as `step`,
    `plan_notification`.`repeat` as `repeat`,
    `plan_notification`.`wait` as `wait`,
    `target_role`.`name` as `role`,
    `target`.`name` as `target`,
    `plan_notification`.`template` as `template`,
    `priority`.`name` as `priority`
FROM `plan_notification`
JOIN `target` ON `plan_notification`.`target_id` = `target`.`id`
JOIN `target_role` ON `plan_notification`.`role_id` = `target_role`.`id`
JOIN `priority` ON `plan_notification`.`priority_id` = `priority`.`id`
WHERE `plan_notification`.`plan_id` = %s
ORDER BY `plan_notification`.`step`'''

template_columns = {
    'id': '`template`.`id` as `id`',
    'name': '`template`.`name` as `name`',
    'creator': '`target`.`name` as `creator`',
    'created': 'UNIX_TIMESTAMP(`template`.`created`) as `created`',
    'active': 'IF(`template_active`.`template_id` IS NULL, FALSE, TRUE) as `active`',
}

template_filters = {
    'id': '`template`.`id`',
    'name': '`template`.`name`',
    'creator': '`target`.`name`',
    'created': '`template`.`created`',
    'active': '`template_active`.`template_id`',
}

template_filter_types = {
    'id': int,
    'created': int,
}

template_query = '''SELECT %s FROM `template`
JOIN `target` ON `template`.`user_id`=`target`.`id`
LEFT OUTER JOIN `template_active` ON `template`.`id` = `template_active`.`template_id`'''

single_template_query = '''SELECT
    `template`.`id` as `id`,
    `template`.`name` as `name`,
    IF(`template_active`.`template_id` IS NULL, FALSE, TRUE) as `active`,
    `target`.`name` as `creator`,
    UNIX_TIMESTAMP(`template`.`created`) as `created`,
    `application`.`name` as `application`,
    `mode`.`name` as `mode`,
    `template_content`.`subject` as `subject`,
    `template_content`.`body` as `body`
FROM `template` JOIN `target` ON `template`.`user_id`=`target`.`id`
LEFT OUTER JOIN `template_active` ON `template`.`id` = `template_active`.`template_id`
JOIN `template_content` ON `template`.`id` = `template_content`.`template_id`
JOIN `application` ON `template_content`.`application_id` = `application`.`id`
JOIN `mode` ON `template_content`.`mode_id` = `mode`.`id`'''

single_template_query_plans = '''SELECT
DISTINCT `plan_active`.`plan_id` as `id`, `plan_active`.`name` as `name`
FROM `plan_notification`
JOIN `plan_active` ON `plan_notification`.`plan_id` = `plan_active`.`plan_id`
WHERE `plan_notification`.`template` = %s'''

insert_plan_query = '''INSERT INTO `plan` (
    `user_id`, `name`, `created`, `description`, `step_count`,
    `threshold_window`, `threshold_count`, `aggregation_window`,
    `aggregation_reset`, `tracking_key`, `tracking_type`, `tracking_template`
) VALUES (
    (SELECT `id` FROM `target` where `name` = :creator AND `type_id` = (
      SELECT `id` FROM `target_type` WHERE `name` = 'user'
    )),
    :name,
    :created,
    :description,
    :step_count,
    :threshold_window,
    :threshold_count,
    :aggregation_window,
    :aggregation_reset,
    :tracking_key,
    :tracking_type,
    :tracking_template
)'''

insert_plan_step_query = '''INSERT INTO `plan_notification` (
    `plan_id`, `step`, `priority_id`, `target_id`, `template`, `role_id`, `repeat`, `wait`
) VALUES (
    :plan_id,
    :step,
    :priority_id,
    (SELECT `target`.`id` FROM `target` WHERE `target`.`name` = :target AND `target`.`type_id` =
      (SELECT `target_role`.`type_id` FROM `target_role` WHERE `id` = :role_id)
    ),
    :template,
    :role_id,
    :repeat,
    :wait
)'''

reprioritization_setting_query = '''SELECT
    `target`.`name` as `target`,
    `mode_src`.`name` as `src_mode`,
    `mode_dst`.`name` as `dst_mode`,
    `target_reprioritization`.`count` as `count`,
    `target_reprioritization`.`duration` as `duration`
FROM `target_reprioritization`
JOIN `target` ON `target`.`id` = `target_reprioritization`.`target_id`
JOIN `target_type` on `target`.`type_id` = `target_type`.`id`
JOIN `mode` `mode_src` ON `mode_src`.`id` = `target_reprioritization`.`src_mode_id`
JOIN `mode` `mode_dst` ON `mode_dst`.`id` = `target_reprioritization`.`dst_mode_id`
WHERE `target`.`name` = %s
AND `target_type`.`name` = 'user'
'''

update_reprioritization_settings_query = '''INSERT INTO target_reprioritization (
    `target_id`, `src_mode_id`, `dst_mode_id`, `count`, `duration`
) VALUES (
    (SELECT `id` FROM `target` WHERE `name` = :target AND `type_id` = (
      SELECT `id` FROM `target_type` WHERE `name` = 'user'
    )),
    :src_mode_id,
    :dst_mode_id,
    :count,
    :duration
) ON DUPLICATE KEY UPDATE `dst_mode_id`=:dst_mode_id,
                          `count`=:count,
                          `duration`=:duration'''

delete_reprioritization_settings_query = '''DELETE
FROM `target_reprioritization`
WHERE `target_id` = (SELECT `id` from `target` where `name` = :target_name AND `type_id` = (
      SELECT `id` FROM `target_type` WHERE `name` = 'user'
    ))
AND `src_mode_id` = (SELECT `id` from `mode` where `name` = :mode_name)'''

get_user_modes_query = '''SELECT
    `priority`.`name` as priority,
    `mode`.`name` as mode from `priority`
JOIN `target_mode` on `target_mode`.`priority_id` = `priority`.`id`
JOIN `mode` on `mode`.`id` = `target_mode`.`mode_id`
JOIN `target` on `target`.`id` =  `target_mode`.`target_id`
WHERE `target`.`name` = :username'''

get_target_application_modes_query = '''SELECT
    `priority`.`name` as priority,
    `mode`.`name` as mode from `priority`
JOIN `target_application_mode` on `target_application_mode`.`priority_id` = `priority`.`id`
JOIN `mode` on `mode`.`id` = `target_application_mode`.`mode_id`
JOIN `target` on `target`.`id` =  `target_application_mode`.`target_id`
JOIN `target_type` on `target`.`type_id` = `target_type`.`id`
JOIN `application` on `application`.`id` = `target_application_mode`.`application_id`
WHERE `target`.`name` = :username
AND `target_type`.`name` = 'user'
AND `application`.`name` = :app'''

get_all_users_app_modes_query = '''SELECT
    `application`.`name` as application,
    `priority`.`name` as priority,
    `mode`.`name` as mode from `priority`
JOIN `target_application_mode` on `target_application_mode`.`priority_id` = `priority`.`id`
JOIN `mode` on `mode`.`id` = `target_application_mode`.`mode_id`
JOIN `application` on `application`.`id` = `target_application_mode`.`application_id`
WHERE `target_application_mode`.`target_id` = %s
'''

get_default_application_modes_query = '''
SELECT `priority`.`name` as priority, `mode`.`name` as mode
FROM `default_application_mode`
JOIN `mode`  on `mode`.`id` = `default_application_mode`.`mode_id`
JOIN `priority` on `priority`.`id` = `default_application_mode`.`priority_id`
JOIN `application` on `application`.`id` = `default_application_mode`.`application_id`
WHERE `application`.`name` = %s'''

get_supported_application_modes_query = '''
SELECT `mode`.`name`
FROM `mode`
JOIN `application_mode` on `mode`.`id` = `application_mode`.`mode_id`
WHERE `application_mode`.`application_id` = %s
'''

insert_user_modes_query = '''INSERT
INTO `target_mode` (`priority_id`, `target_id`, `mode_id`)
VALUES (
    (SELECT `id` from `priority` WHERE `name` = :priority),
    (SELECT `id` from `target` WHERE `name` = :name AND `type_id` = (
      SELECT `id` FROM `target_type` WHERE `name` = 'user'
    )),
    (SELECT `id` from `mode` WHERE `name` = :mode))
ON DUPLICATE KEY UPDATE
    `target_mode`.`mode_id` = (SELECT `id` from `mode` WHERE `name` = :mode)'''

delete_user_modes_query = '''DELETE FROM `target_mode`
WHERE `target_id` = (SELECT `id` from `target` WHERE `name` = :name AND `type_id` =
                    (SELECT `id` FROM `target_type` WHERE `name` = 'user'))
AND `priority_id` = (SELECT `id` from `priority` WHERE `name` = :priority)'''

insert_target_application_modes_query = '''INSERT
INTO `target_application_mode`
    (`priority_id`, `target_id`, `mode_id`, `application_id`)
VALUES (
    (SELECT `id` from `priority` WHERE `name` = :priority),
    (SELECT `id` from `target` WHERE `name` = :name AND `target`.`type_id` = (
      SELECT `id` FROM `target_type` WHERE `name` = 'user'
    )),
    (SELECT `id` from `mode` WHERE `name` = :mode),
    (SELECT `id` from `application` WHERE `name` = :app))
ON DUPLICATE KEY UPDATE
    `target_application_mode`.`mode_id` = (SELECT `id` from `mode` WHERE `name` = :mode)'''

delete_target_application_modes_query = '''DELETE FROM `target_application_mode`
WHERE `target_id` = (SELECT `id` from `target` WHERE `name` = :name AND `type_id` = (
      SELECT `id` FROM `target_type` WHERE `name` = 'user'
    )) AND
      `priority_id` = (SELECT `id` from `priority` WHERE `name` = :priority) AND
      `application_id` = (SELECT `id` from `application` WHERE `name` = :app)'''

get_applications_query = '''SELECT
    `id`, `name`, `context_template`, `sample_context`, `summary_template`
FROM `application`
WHERE `auth_only` is False'''

get_vars_query = 'SELECT `name`, `required` FROM `template_variable` WHERE `application_id` = %s ORDER BY `required` DESC, `name` ASC'

get_allowed_roles_query = '''SELECT `target_role`.`id`
                             FROM `target_role`
                             JOIN `target_type` ON `target_type`.`id` = `target_role`.`type_id`
                             JOIN `target` ON `target`.`type_id` = `target_type`.`id`
                             WHERE `target`.`name` = :target'''

check_username_admin_query = '''SELECT `user`.`admin`
                                FROM `user`
                                JOIN `target` ON `target`.`id` = `user`.`target_id`
                                JOIN `target_type` ON `target_type`.`id` = `target`.`type_id`
                                WHERE `target`.`name` = %s
                                AND `target_type`.`name` = "user"'''

check_application_ownership_query = '''SELECT 1
                                       FROM `application_owner`
                                       JOIN `target` on `target`.`id` = `application_owner`.`user_id`
                                       WHERE `target`.`name` = :username
                                       AND `application_owner`.`application_id` = :application_id'''

get_application_owners_query = '''SELECT `target`.`name`
                                  FROM `application_owner`
                                  JOIN `target` on `target`.`id` = `application_owner`.`user_id`
                                  WHERE `application_owner`.`application_id` = %s'''

uuid4hex = re.compile('[0-9a-f]{32}\Z', re.I)


def stream_incidents_with_context(cursor):
    for row in cursor:
        row['context'] = ujson.loads(row['context'])
        yield row


def get_app_from_msg_id(session, msg_id):
    sql = '''SELECT `application`.`name` FROM `message`
             JOIN `application` on `application`.`id` = `message`.`application_id`
             WHERE `message`.`id` = :msg_id'''
    result = session.execute(sql, {'msg_id': msg_id}).scalar()

    if result:
        return result
    else:
        return None


def is_valid_tracking_settings(t, k, tpl):
    if not t:
        if k or tpl:
            return False, 'Incomplete tracking setting'
        else:
            # no tracking setting
            return True, None
    if not (k and tpl):
        return False, 'Incomplete tracking setting'
    if not isinstance(tpl, dict) or not tpl:
        return False, 'Template must be a dictionary'
    if t == 'email':
        if '@' not in k:
            return False, 'Invalid email address'
        for app in tpl:
            if not tpl[app]:
                return False, 'No key for %s template' % app
            missed_keys = set(('email_subject', 'email_text')) - set(tpl[app])
            if missed_keys:
                return False, 'Missing keys for %s template: %s' % (app, missed_keys)
    else:
        return False, 'Unknown tracking type: %s' % t
    return True, None


def gen_where_filter_clause(connection, filters, filter_types, kwargs):
    '''
    How each where clauses are generated:
        1. find out column part through filters[col], skipping nonexistent columns that
           might exist from invalid 'fields' parameters
        2. find out operator part through operators[op]
        3. escape value through connection.escape(filter_types.get(col, str)(value))
        4. (optional) transform escaped value through filter_escaped_value_transforms[col](value)
    '''
    where = []
    for key, values in kwargs.iteritems():
        col, _, op = key.partition('__')
        # Skip columns that don't exist
        if col not in filters:
            continue
        col_type = filter_types.get(col, str)
        # Format strings because Falcon splits on ',' but not on '%2C'
        # TODO: Get rid of this by setting request options on Falcon 1.1
        if isinstance(values, basestring):
            values = values.split(',')
        for val in values:
            try:
                if op == 'in':
                    if len(values) == 1:
                        op = 'eq'
                        val = col_type(values[0])
                    else:
                        val = tuple([col_type(v) for v in values])
                else:
                    val = col_type(val)
            except (ValueError, TypeError):
                raise HTTPBadRequest('invalid argument type',
                                     '%s should be %s' % (col, col_type))
            val = connection.escape(val)
            if col in filter_escaped_value_transforms:
                val = filter_escaped_value_transforms[col](val)
            where.append(operators[op] % (filters[col], val))
    return where


class HeaderMiddleware(object):
    def process_request(self, req, resp):
        resp.content_type = 'application/json'
        resp.set_headers([XFRAME, XCONTENTTYPEOPTIONS, XXSSPROTECTION])


class ReqBodyMiddleware(object):
    '''
    Falcon's req object has a stream that we read to obtain the post body.
    However, we can only read this once, and we often need the post body twice
    (once for authentication and once in the handler method). To avoid this
    problem, we read the post body into the request context and access it from
    there.

    IMPORTANT NOTE: Because we use stream.read() here, all other uses of this
    method will return '', not the post body.
    '''

    def process_request(self, req, resp):
        req.context['body'] = req.stream.read()


class AuthMiddleware(object):
    def __init__(self, debug=False):
        if debug:
            self.process_resource = self.debug_auth

    def debug_auth(self, req, resp, resource, params):
        req.context['username'] = req.env.get('beaker.session', {}).get('user', None)
        method = req.method

        if resource.allow_read_no_auth and method == 'GET':
            return

        # If we're authenticated using beaker, don't validate app as if this is an
        # API call, but set 'app' to the internal iris user as some routes (test incident creation)
        # need it.
        if req.context['username']:
            req.context['app'] = cache.applications.get('iris')
            return

        # For the purpose of e2etests, allow setting username via header, rather than going
        # through beaker
        username_header = req.get_header('X-IRIS-USERNAME')
        if username_header:
            req.context['username'] = username_header
            return

        # If this is a frontend route, and we're not logged in, don't fall through to process as
        # an app. This will allow the ACLMiddleware to force the login page.
        if getattr(resource, 'frontend_route', False):
            return

        # Proceed with authenticating this route as a third party application
        try:
            app, client_digest = req.get_header('AUTHORIZATION', '')[5:].split(':', 1)
            if app not in cache.applications:
                logger.warn('Tried authenticating with nonexistent app, %s', app)
                raise HTTPUnauthorized('Authentication failure', 'Application not found', [])
            req.context['app'] = cache.applications[app]
        except TypeError:
            return

    def process_resource(self, req, resp, resource, params):  # pragma: no cover
        req.context['username'] = req.env.get('beaker.session', {}).get('user', None)
        method = req.method

        if resource.allow_read_no_auth and method == 'GET':
            return

        # If we're authenticated using beaker, don't validate app as if this is an
        # API call, but set 'app' to the internal iris user as some routes (test incident creation)
        # need it.
        if req.context['username']:
            req.context['app'] = cache.applications.get('iris')
            return

        # If this is a frontend route, and we're not logged in, don't fall through to process as
        # an app either. This will allow the ACLMiddleware to force the login page.
        if getattr(resource, 'frontend_route', False):
            return

        # Proceed with authenticating this route as a third party application, and enforce
        # hmac for the entire request, and still allow the username-by-header functionality
        # if we're being hit from an instance of iris-frontend
        path = req.env['PATH_INFO']
        qs = req.env['QUERY_STRING']
        if qs:
            path = path + '?' + qs
        body = req.context['body']
        auth = req.get_header('AUTHORIZATION')
        if auth and auth.startswith('hmac '):
            username_header = req.get_header('X-IRIS-USERNAME')
            try:
                app_name, client_digest = auth[5:].split(':', 1)
                app = cache.applications.get(app_name)
                if not app:
                    logger.warn('Tried authenticating with nonexistent app, %s', app_name)
                    raise HTTPUnauthorized('Authentication failure', '', [])
                if username_header and not app['allow_authenticating_users']:
                    logger.warn('Unprivileged application %s tried authenticating %s', app['name'], username_header)
                    raise HTTPUnauthorized('This application does not have the power to authenticate usernames', '', [])
                api_key = str(app['key'])
                window = int(time.time()) // 5
                # If username header is present, throw that into the hmac validation as well
                if username_header:
                    text = '%s %s %s %s %s' % (window, method, path, body, username_header)
                else:
                    text = '%s %s %s %s' % (window, method, path, body)
                HMAC = hmac.new(api_key, text, hashlib.sha512)
                digest = base64.urlsafe_b64encode(HMAC.digest())
                if equals(client_digest, digest):
                    req.context['app'] = app
                    if username_header:
                        req.context['username'] = username_header
                    return
                else:
                    if username_header:
                        text = '%s %s %s %s %s' % (window - 1, method, path, body, username_header)
                    else:
                        text = '%s %s %s %s' % (window - 1, method, path, body)
                    HMAC = hmac.new(api_key, text, hashlib.sha512)
                    digest = base64.urlsafe_b64encode(HMAC.digest())
                    if equals(client_digest, digest):
                        req.context['app'] = app
                        if username_header:
                            req.context['username'] = username_header
                    else:
                        if username_header:
                            logger.warn('HMAC doesn\'t validate for app %s (passing username %s)', app['name'], username_header)
                        else:
                            logger.warn('HMAC doesn\'t validate for app %s', app['name'])
                        raise HTTPUnauthorized('Authentication failure', '', [])

            except (ValueError, KeyError):
                logger.exception('Authentication failure')
                raise HTTPUnauthorized('Authentication failure', '', [])

        else:
            logger.warn('Request has malformed/missing HMAC authorization header')
            raise HTTPUnauthorized('Authentication failure', '', [])


class ACLMiddleware(object):
    def __init__(self, debug):
        pass

    def process_resource(self, req, resp, resource, params):
        self.process_frontend_routes(req, resource)
        self.process_admin_acl(req, resource, params)

    def process_frontend_routes(self, req, resource):
        if req.context['username']:
            # Logged in and looking at /login page? Redirect to home.
            if req.path == '/login':
                raise HTTPFound(ui.default_route)
        else:
            # If we're not logged in and this is a frontend route, we're only allowed
            # to view the login form
            if getattr(resource, 'frontend_route', False):
                if req.path != '/login':
                    raise HTTPFound(ui.login_url(req))

    def process_admin_acl(self, req, resource, params):
        req.context['is_admin'] = False

        # Quickly check the username in the path matches who's logged in
        enforce_user = getattr(resource, 'enforce_user', False)

        if not req.context['username']:
            if enforce_user:
                raise HTTPUnauthorized('Username must be specified for this action', '', [])
            return

        # Check if user is an admin
        connection = db.engine.raw_connection()
        cursor = connection.cursor()
        cursor.execute(check_username_admin_query, req.context['username'])
        result = cursor.fetchone()
        cursor.close()
        connection.close()

        if result:
            req.context['is_admin'] = bool(result[0])

        if enforce_user and not req.context['is_admin']:
            path_username = params.get('username')
            if not equals(path_username, req.context['username']):
                raise HTTPUnauthorized('This user is not allowed to access this resource', '', [])


class Plan(object):
    allow_read_no_auth = True

    def on_get(self, req, resp, plan_id):
        if plan_id.isdigit():
            where = 'WHERE `plan`.`id` = %s'
        else:
            where = 'WHERE `plan`.`name` = %s AND `plan_active`.`plan_id` IS NOT NULL'
        query = single_plan_query + where

        connection = db.engine.raw_connection()
        cursor = connection.cursor(db.dict_cursor)
        cursor.execute(query, plan_id)
        plan = cursor.fetchone()

        if plan:
            step = 0
            steps = []
            cursor.execute(single_plan_query_steps, plan['id'])
            for notification in cursor:
                s = notification['step']
                if s != step:
                    l = [notification]
                    steps.append(l)
                    step = s
                else:
                    l.append(notification)
            plan['steps'] = steps
            if plan['tracking_template']:
                plan['tracking_template'] = ujson.loads(plan['tracking_template'])

            resp.body = ujson.dumps(plan)
            connection.close()
        else:
            connection.close()
            raise HTTPNotFound()

    def on_post(self, req, resp, plan_id):
        session = db.Session()
        try:
            post_body = ujson.loads(req.context['body'])
            try:
                active = int(post_body['active'])
            except KeyError:
                raise HTTPBadRequest('"active" field required', '')
            except ValueError:
                raise HTTPBadRequest('Invalid active field', '')
            if active:
                session.execute('''INSERT INTO `plan_active` (`name`, `plan_id`)
                                   VALUES ((SELECT `name` FROM `plan` WHERE `id` = :plan_id), :plan_id)
                                   ON DUPLICATE KEY UPDATE `plan_id`=:plan_id''',
                                {'plan_id': plan_id})
            else:
                session.execute('DELETE FROM `plan_active` WHERE `plan_id`=:plan_id', {'plan_id': plan_id})
            session.commit()
            session.close()
            resp.status = HTTP_200
            resp.body = ujson.dumps(active)
        except HTTPBadRequest:
            raise
        except Exception:
            session.close()
            logger.exception('ERROR')
            raise

    def on_delete(self, req, resp, plan_id):
        if not req.context['username']:
            raise HTTPUnauthorized('You must be a logged in user to delete unused plans', '')

        if plan_id.isdigit():
            query = '''SELECT EXISTS(SELECT 1 FROM `plan` WHERE `id` = %s)'''
            plan_name = None
        else:
            query = '''SELECT EXISTS(SELECT 1 FROM `plan` WHERE `name` = %s)'''
            plan_name = plan_id

        connection = db.engine.raw_connection()
        cursor = connection.cursor()
        cursor.execute(query, plan_id)
        result = cursor.fetchone()

        if not result[0]:
            connection.close()
            raise HTTPBadRequest('No plan matched', '')

        if not plan_name:
            cursor.execute('SELECT `name` FROM `plan` WHERE `id` = %s', plan_id)
            result = cursor.fetchone()
            if not result:
                connection.close()
                raise HTTPBadRequest('Could not resolve this plan_id to name', '')
            plan_name = result[0]

        # Check if any quota is using these.
        cursor.execute('''SELECT `application`.`name`
                          FROM `application_quota`
                          JOIN `application` on `application`.`id` = `application_quota`.`application_id`
                          WHERE `application_quota`.`plan_name` = %s''', plan_name)
        result = cursor.fetchone()

        if result:
            connection.close()
            raise HTTPBadRequest('Cannot delete this plan as the application %s is using it for quota' % result[0], '')

        # Check if any incidents were made with these plan IDs. If they were, fail
        cursor.execute('SELECT COUNT(*) FROM `incident` WHERE `plan_id` IN (SELECT `id` FROM `plan` WHERE `name` = %s)', plan_name)
        result = cursor.fetchone()

        if result[0]:
            connection.close()
            raise HTTPBadRequest('Cannot delete this plan as %s incidents have been created using it' % result[0], '')

        # Delete all steps
        try:
            cursor.execute('DELETE FROM `plan_notification` WHERE `plan_id` IN (SELECT `id` FROM `plan` WHERE `name` = %s)', plan_name)
        except IntegrityError:
            connection.close()
            raise HTTPBadRequest('Failed deleting plan steps', '')

        # Purge plan_active
        try:
            cursor.execute('DELETE FROM `plan_active` WHERE `name` = %s', plan_name)
        except IntegrityError:
            connection.close()
            raise HTTPBadRequest('Failed deleting plan steps', '')

        # Delete all matching plans
        try:
            cursor.execute('DELETE FROM `plan` WHERE `name` = %s', plan_name)
        except IntegrityError:
            connection.close()
            raise HTTPBadRequest('Failed deleting plans. It is likely still in use.', '')

        connection.commit()
        connection.close()

        logger.info('%s deleted plan %s', req.context['username'], plan_name)

        resp.status = HTTP_200
        resp.body = '[]'


class Plans(object):
    allow_read_no_auth = True

    def on_get(self, req, resp):
        '''
        Plan search endpoint.

        **Example request**:

        .. sourcecode:: http

           GET /v0/plans?name__contains=foo&active=1 HTTP/1.1

          **Example response**:

          .. sourcecode:: http

             HTTP/1.1 200 OK
             Content-Type: application/json

             [
                 {
                     "description": "This is plan foo",
                     "threshold_count": 10,
                     "creator": "user1",
                     "created": 1478154275,
                     "aggregation_reset": 300,
                     "aggregation_window": 300,
                     "threshold_window": 900,
                     "tracking_type": null,
                     "tracking_template": null,
                     "tracking_key": null,
                     "active": 1,
                     "id": 123456,
                     "name": "foo-sla0"
                 }
             ]
          '''
        query_limit = req.get_param_as_int('limit')
        req.params.pop('limit', None)
        fields = req.get_param_as_list('fields')
        fields = [f for f in fields if f in plan_columns] if fields else None
        req.params.pop('fields', None)
        if not fields:
            fields = plan_columns

        query = plan_query % ', '.join(plan_columns[f] for f in fields)

        where = []
        active = req.get_param_as_bool('active')
        req.params.pop('active', None)
        if active is not None:
            if active:
                where.append('`plan_active`.`plan_id` IS NOT NULL')
            else:
                where.append('`plan_active`.`plan_id` IS NULL')

        connection = db.engine.raw_connection()
        where += gen_where_filter_clause(
            connection, plan_filters, plan_filter_types, req.params)

        if where:
            query = query + ' WHERE ' + ' AND '.join(where)

        if query_limit is not None:
            query += ' ORDER BY `plan`.`created` DESC LIMIT %s' % query_limit

        cursor = connection.cursor(db.dict_cursor)
        cursor.execute(query)

        payload = ujson.dumps(cursor)
        connection.close()
        resp.status = HTTP_200
        resp.body = payload

    def on_post(self, req, resp):
        plan_params = ujson.loads(req.context['body'])
        session = db.Session()
        try:
            run_validation('plan', plan_params)
            now = datetime.datetime.utcnow()
            plan_name = plan_params['name']
            # FIXME: catch creator not exist error

            tracking_key = plan_params.get('tracking_key')
            tracking_type = plan_params.get('tracking_type')
            tracking_template = plan_params.get('tracking_template')
            is_valid, err_msg = is_valid_tracking_settings(tracking_type, tracking_key, tracking_template)
            if not is_valid:
                raise HTTPBadRequest('Invalid tracking template', err_msg)

            if tracking_template:
                tracking_template = ujson.dumps(tracking_template)
            else:
                tracking_template = None  # in case tracking_template is an empty dict
            plan_dict = {
                'creator': plan_params['creator'],
                'name': plan_name,
                'created': now,
                'description': plan_params['description'],
                'step_count': len(plan_params['steps']),
                'threshold_window': plan_params['threshold_window'],
                'threshold_count': plan_params['threshold_count'],
                'aggregation_window': plan_params['aggregation_window'],
                'aggregation_reset': plan_params['aggregation_reset'],
                'tracking_key': tracking_key,
                'tracking_type': tracking_type,
                'tracking_template': tracking_template,
            }

            plan_id = session.execute(insert_plan_query, plan_dict).lastrowid

            for index, steps in enumerate(plan_params['steps'], start=1):
                for step in steps:
                    step['plan_id'] = plan_id
                    step['step'] = index
                    priority = cache.priorities.get(step['priority'])
                    role = cache.target_roles.get(step['role'])

                    if priority:
                        step['priority_id'] = priority['id']
                    else:
                        raise HTTPBadRequest('Invalid plan', 'Priority not found for step %s' % index)
                    if role:
                        step['role_id'] = role
                    else:
                        raise HTTPBadRequest('Invalid plan', 'Role not found for step %s' % index)

                    allowed_roles = {row[0] for row in session.execute(get_allowed_roles_query, step)}

                    if not allowed_roles:
                        raise HTTPBadRequest('Invalid plan', 'Target %s not found for step %s' % (step['target'], index))

                    if role not in allowed_roles:
                        raise HTTPBadRequest('Invalid role', 'Role %s is not appropriate for target %s in step %s' % (
                                             step['role'], step['target'], index))

                    try:
                        session.execute(insert_plan_step_query, step)
                    except IntegrityError:
                        raise HTTPBadRequest('Invalid plan', 'Target not found for step %s' % index)

            session.execute('INSERT INTO `plan_active` (`name`, `plan_id`) '
                            'VALUES (:name, :plan_id) ON DUPLICATE KEY UPDATE `plan_id`=:plan_id',
                            {'name': plan_name, 'plan_id': plan_id})

            session.commit()
            session.close()
            resp.status = HTTP_201
            resp.body = ujson.dumps(plan_id)
            resp.set_header('Location', '/plans/%s' % plan_id)
        except IrisValidationException as e:
            session.close()
            raise HTTPBadRequest('Validation error', str(e))
        except HTTPBadRequest:
            session.close()
            raise
        except Exception:
            session.close()
            logger.exception('ERROR')
            raise


class Incidents(object):
    allow_read_no_auth = True

    def on_get(self, req, resp):
        fields = req.get_param_as_list('fields')
        req.params.pop('fields', None)
        if not fields:
            fields = incident_columns
        req.params.pop('fields', None)
        query_limit = req.get_param_as_int('limit')
        req.params.pop('limit', None)
        target = req.get_param_as_list('target')
        req.params.pop('target', None)

        query = incident_query % ', '.join(incident_columns[f] for f in fields)

        connection = db.engine.raw_connection()
        where = gen_where_filter_clause(connection, incident_filters, incident_filter_types, req.params)
        sql_values = []
        if target:
            where.append('''`incident`.`id` IN (
                SELECT `incident_id`
                FROM `message`
                JOIN `target` ON `message`.`target_id`=`target`.`id`
                WHERE `target`.`name` IN %s
            )''')
            sql_values.append(tuple(target))
        if where:
            query = query + ' WHERE ' + ' AND '.join(where)
        if query_limit is not None:
            query += ' ORDER BY `incident`.`created` DESC LIMIT %s' % query_limit

        cursor = connection.cursor(db.dict_cursor)
        cursor.execute(query, sql_values)

        if 'context' in fields:
            payload = ujson.dumps(stream_incidents_with_context(cursor))
        else:
            payload = ujson.dumps(cursor)
        connection.close()
        resp.status = HTTP_200
        resp.body = payload

    def on_post(self, req, resp):
        '''
        Create incidents. Id for the new incident will be returned.

        **Example request**:

        .. sourcecode:: http

           POST /v0/incidents HTTP/1.1
           Content-Type: application/json

           {
               "plan": "test-plan",
               "context": {"number": 1, "str": "hello"}
           }

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 201 Created
           Content-Type: application/json

           1

        :statuscode 201: incident created
        :statuscode 400: invalid request
        :statuscode 404: plan not found
        :statuscode 401: application is not allowed to create incident for other application

        A request is considered invalid if:

        - plan name is missing
        - application is invalid
        - context json blob is longer than 655355 bytes
        - none of the templates used in the plan supports the given application
        '''
        session = db.Session()
        incident_params = ujson.loads(req.context['body'])
        if 'plan' not in incident_params:
            session.close()
            raise HTTPBadRequest('missing plan name attribute', '')

        plan_id = session.execute('SELECT `plan_id` FROM `plan_active` WHERE `name` = :plan',
                                  {'plan': incident_params['plan']}).scalar()
        if not plan_id:
            logger.warn('Plan "%s" not found.', incident_params['plan'])
            session.close()
            raise HTTPNotFound()

        app = req.context['app']

        if 'application' in incident_params:
            if not req.context['app']['allow_other_app_incidents']:
                raise HTTPForbidden('This application %s does not allow creating incidents as other applications' % req.context['app']['name'], '')

            app = cache.applications.get(incident_params['application'])

            if not app:
                raise HTTPBadRequest('Invalid application', '')

        try:
            context = incident_params['context']
            context_json_str = ujson.dumps({variable: context.get(variable)
                                           for variable in app['variables']})
            if len(context_json_str) > 65535:
                raise HTTPBadRequest('Context too long', '')

            app_template_count = session.execute('''
                SELECT EXISTS (
                  SELECT 1 FROM
                  `plan_notification`
                  JOIN `template` ON `template`.`name` = `plan_notification`.`template`
                  JOIN `template_content` ON `template_content`.`template_id` = `template`.`id`
                  WHERE `plan_notification`.`plan_id` = :plan_id
                  AND `template_content`.`application_id` = :app_id
                )
            ''', {'app_id': app['id'], 'plan_id': plan_id}).scalar()

            if not app_template_count:
                raise HTTPBadRequest('No plan template actions exist for this app', '')

            data = {
                'plan_id': plan_id,
                'created': datetime.datetime.utcnow(),
                'application_id': app['id'],
                'context': context_json_str,
                'current_step': 0,
                'active': True,
            }

            incident_id = session.execute(
                '''INSERT INTO `incident` (`plan_id`, `created`, `context`, `current_step`, `active`, `application_id`)
                   VALUES (:plan_id, :created, :context, 0, :active, :application_id)''',
                data).lastrowid

            session.commit()
            session.close()
            resp.status = HTTP_201
            resp.set_header('Location', '/incidents/%s' % incident_id)
            resp.body = ujson.dumps(incident_id)
        except HTTPBadRequest:
            raise
        except Exception:
            session.close()
            logger.exception('ERROR')
            raise


class Incident(object):
    allow_read_no_auth = True

    def on_get(self, req, resp, incident_id):
        '''
        Get incident by ID.

        **Example request**:

        .. sourcecode:: http

           GET /v0/incident/1 HTTP/1.1

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           {
               "updated": 1492057026,
               "plan_id": 48271,
               "created": 1492055912,
               "application": "Alert manager",
               "steps": [
                    {
                        "name": "alice",
                        "created": 1492055953,
                        "target_changed": 0,
                        "mode_changed": 0,
                        "priority": "urgent",
                        "step": 1,
                        "mode": "sms",
                        "id": 25443689,
                        "sent": 1492055957
                    }
               ],
               "plan": "test-plan",
               "context": {"number": 1, "str": "hello"},
               "owner": "alice",
               "active": 0,
               "id": 1,
               "current_step": 1
           }
        '''
        connection = db.engine.raw_connection()
        cursor = connection.cursor(db.dict_cursor)
        try:
            cursor.execute(single_incident_query, int(incident_id))
        except ValueError:
            raise HTTPBadRequest('Invalid incident id', '')
        incident = cursor.fetchone()

        if incident:
            cursor.execute(single_incident_query_steps, (auditlog.MODE_CHANGE, auditlog.TARGET_CHANGE, incident['id']))
            incident['steps'] = cursor.fetchall()
            connection.close()

            incident['context'] = ujson.loads(incident['context'])
            payload = ujson.dumps(incident)
        else:
            connection.close()
            raise HTTPNotFound()
        resp.status = HTTP_200
        resp.body = payload

    def on_post(self, req, resp, incident_id):
        incident_params = ujson.loads(req.context['body'])

        try:
            owner = incident_params['owner']
        except KeyError:
            raise HTTPBadRequest('"owner" field required', '')

        session = db.Session()
        try:
            is_active = utils.claim_incident(incident_id, owner, session)
            resp.status = HTTP_200
            resp.body = ujson.dumps({'incident_id': int(incident_id),
                                     'owner': owner,
                                     'active': is_active})
        except Exception:
            session.close()
            logger.exception('ERROR')
            raise


class Message(object):
    allow_read_no_auth = True

    def on_get(self, req, resp, message_id):
        '''
        Get information for an iris message by id

        **Example request**:

        .. sourcecode:: http

           GET /v0/messages/{message_id} HTTP/1.1

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           {
              "body": "message body",
              "incident_id": 2590447,
              "target": "username",
              "created": 1490825218,
              "destination": "username@domain.com",
              "batch": null,
              "twilio_delivery_status": null,
              "priority": "low",
              "application": "app",
              "mode": "email",
              "active": 0,
              "generic_message_sent_status": 1,
              "id": 24807074,
              "sent": 1490825221,
              "subject": "message subject"
           }
        '''
        connection = db.engine.raw_connection()
        cursor = connection.cursor(db.dict_cursor)
        cursor.execute(single_message_query, int(message_id))
        message = cursor.fetchone()
        connection.close()
        if message:
            resp.body = ujson.dumps(message)
        else:
            raise HTTPNotFound()
        resp.status = HTTP_200


class MessageAuditLog(object):
    allow_read_no_auth = True

    def on_get(self, req, resp, message_id):
        '''
        Get a message's log of changes

        **Example request**:

        .. sourcecode:: http

           GET /v0/messages/{message_id}/auditlog HTTP/1.1

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           [
             {
               "old": "sms",
               "description": "Changing mode due to original mode failure",
               "date": 1489507284,
               "new": "email",
               "change_type": "mode-change",
               "id": 438
             },
           ]
        '''
        connection = db.engine.raw_connection()
        cursor = connection.cursor(db.dict_cursor)
        cursor.execute(message_audit_log_query, int(message_id))
        resp.body = ujson.dumps(cursor)
        connection.close()


class Messages(object):
    allow_read_no_auth = True

    def on_get(self, req, resp):
        fields = req.get_param_as_list('fields')
        req.params.pop('fields', None)
        fields = [f for f in fields if f in message_columns] if fields else None
        if not fields:
            fields = message_columns
        query_limit = req.get_param_as_int('limit')
        req.params.pop('limit', None)

        connection = db.engine.raw_connection()
        escaped_params = {
            'mode_change': connection.escape(auditlog.MODE_CHANGE),
            'target_change': connection.escape(auditlog.TARGET_CHANGE)
        }

        query = message_query % ', '.join(message_columns[f] % escaped_params for f in fields)

        where = gen_where_filter_clause(connection, message_filters, message_filter_types, req.params)
        if where:
            query = query + ' WHERE ' + ' AND '.join(where)

        if query_limit is not None:
            query += ' ORDER BY `message`.`created` DESC LIMIT %s' % query_limit
        cursor = connection.cursor(db.dict_cursor)
        cursor.execute(query)
        resp.body = ujson.dumps(cursor)
        connection.close()


class Notifications(object):
    allow_read_no_auth = False
    required_attrs = frozenset(['target', 'role', 'subject'])

    def __init__(self, sender_addr):
        self.sender_addr = sender_addr
        logger.info('Sender used for notifications: %s:%s', *self.sender_addr)

    def on_post(self, req, resp):
        '''
        Create out of band notifications. Notification is ad-hoc message that's
        not tied to an incident. To achieve real-time delivery, notifications
        are not persisted in the Database.

        You can set the priority key to honor target's priority preference or
        set the mode key to force the message transport.

        **Example request**:

        .. sourcecode:: http

           POST /v0/notifications HTTP/1.1
           Content-Type: application/json

           {
               "role": "secondary-oncall",
               "target": "test_oncall_team",
               "subject": "wake up",
               "body": "something is on fire",
               "priority": "high"
           }

        .. sourcecode:: http

           POST /v0/notifications HTTP/1.1
           Content-Type: application/json

           {
               "role": "user",
               "target": "test_user",
               "subject": "wake up",
               "body": "something is on fire",
               "mode": "email"
           }

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           []

        :statuscode 200: notification send request queued
        :statuscode 400: invalid request
        :statuscode 401: application is not allowed to create out of band notification

        A request is considered invalid if:

        - either target, subject or role is missing
        - both priority and mode are missing
        - invalid priority, mode
        - both tempalte, body and email_html are missing
        - template, body and email_html is not a string
        - message queue request rejected by sender
        '''

        message = ujson.loads(req.context['body'])
        msg_attrs = set(message)
        if not msg_attrs >= self.required_attrs:
            raise HTTPBadRequest('Missing required atrributes',
                                 ', '.join(self.required_attrs - msg_attrs))

        # If both priority and mode are passed in, priority overrides mode
        if 'priority' in message:
            priority = cache.priorities.get(message['priority'])
            if not priority:
                raise HTTPBadRequest('Invalid priority', message['priority'])
            message['priority_id'] = priority['id']
        elif 'mode' in message:
            mode_id = cache.modes.get(message['mode'])
            if not mode_id:
                raise HTTPBadRequest('Invalid mode', message['mode'])
            message['mode_id'] = mode_id
        else:
            raise HTTPBadRequest(
                'Both priority and mode are missing, at least one of it is required', '')

        # Avoid problems down the line if we have no way of creating the
        # message body, which happens if both body and template are not
        # specified, or if we don't have email_html
        if 'template' in message:
            if not isinstance(message['template'], basestring):
                raise HTTPBadRequest('template needs to be a string', '')
        elif 'body' in message:
            if not isinstance(message['body'], basestring):
                raise HTTPBadRequest('body needs to be a string', '')
        elif 'email_html' in message:
            if not isinstance(message['email_html'], basestring):
                raise HTTPBadRequest('email_html needs to be a string', '')
            # Handle the edge-case where someone is only specifying email_html
            # and not the others. Avoid KeyError's later on in sender
            if message.get('body') is None:
                message['body'] = ''
        else:
            raise HTTPBadRequest('body, template, and email_html are missing, so we cannot construct message.', '')

        message['application'] = req.context['app']['name']
        s = socket.create_connection(self.sender_addr)
        s.send(msgpack.packb({'endpoint': 'v0/send', 'data': message}))
        sender_resp = utils.msgpack_unpack_msg_from_socket(s)
        s.close()
        if sender_resp == 'OK':
            resp.status = HTTP_200
            resp.body = '[]'
        else:
            logger.warning('OOB message (%s) rejected by sender because %s', message, sender_resp)
            raise HTTPBadRequest('Request rejected by sender', sender_resp)


class Template(object):
    allow_read_no_auth = True

    def on_get(self, req, resp, template_id):
            if template_id.isdigit():
                where = 'WHERE `template`.`id` = %s'
            else:
                where = 'WHERE `template`.`name` = %s AND `template_active`.`template_id` IS NOT NULL'
            query = single_template_query + where

            connection = db.engine.raw_connection()
            cursor = connection.cursor()
            cursor.execute(query, template_id)
            results = cursor.fetchall()

            if results:
                r = results[0]
                t = {
                    'id': r[0],
                    'name': r[1],
                    'active': r[2],
                    'creator': r[3],
                    'created': r[4]
                }
                content = {}
                for r in results:
                    content.setdefault(r[5], {})[r[6]] = {'subject': r[7], 'body': r[8]}
                t['content'] = content
                cursor = connection.cursor(db.dict_cursor)
                cursor.execute(single_template_query_plans, t['name'])
                t['plans'] = cursor.fetchall()
                connection.close()
                payload = ujson.dumps(t)
            else:
                raise HTTPNotFound()
            resp.status = HTTP_200
            resp.body = payload

    def on_post(self, req, resp, template_id):
        session = db.Session()
        template_params = ujson.loads(req.context['body'])
        try:
            try:
                active = int(template_params['active'])
            except ValueError:
                raise HTTPBadRequest('Invalid active argument', 'active must be an int')
            except KeyError:
                raise HTTPBadRequest('Missing active argument', '')
            if active:
                session.execute('''INSERT INTO `template_active` (`name`, `template_id`)
                                   VALUES ((SELECT `name` FROM `template` WHERE `id` = :template_id), :template_id)
                                   ON DUPLICATE KEY UPDATE `template_id`=:template_id''',
                                {'template_id': template_id})
            else:
                session.execute('DELETE FROM `template_active` WHERE `template_id`=:template_id',
                                {'template_id': template_id})
            session.commit()
            session.close()
            resp.status = HTTP_200
            resp.body = ujson.dumps(active)
        except HTTPBadRequest:
            raise
        except Exception:
            session.close()
            logger.exception('ERROR')
            raise


class Templates(object):
    allow_read_no_auth = True

    def on_get(self, req, resp):
        query_limit = req.get_param_as_int('limit')
        req.params.pop('limit', None)
        fields = req.get_param_as_list('fields')
        fields = [f for f in fields if f in template_columns] if fields else None
        if not fields:
            fields = template_columns
        req.params.pop('fields', None)

        query = template_query % ', '.join(template_columns[f] for f in fields)

        where = []
        active = req.get_param_as_bool('active')
        req.params.pop('active', None)
        if active is not None:
            if active:
                where.append('`template_active`.`template_id` IS NOT NULL')
            else:
                where.append('`template_active`.`template_id` IS NULL')

        connection = db.engine.raw_connection()
        where += gen_where_filter_clause(connection, template_filters, template_filter_types, req.params)

        if where:
            query = query + ' WHERE ' + ' AND '.join(where)

        if query_limit is not None:
            query += ' ORDER BY `template`.`created` DESC LIMIT %s' % query_limit

        cursor = connection.cursor(db.dict_cursor)
        cursor.execute(query)

        payload = ujson.dumps(cursor)
        connection.close()
        resp.status = HTTP_200
        resp.body = payload

    def on_post(self, req, resp):
        session = db.Session()
        try:
            template_params = ujson.loads(req.context['body'])
            if 'content' not in template_params:
                raise HTTPBadRequest('content argument missing', '')
            if 'name' not in template_params:
                raise HTTPBadRequest('name argument missing', '')
            if 'creator' not in template_params:
                raise HTTPBadRequest('creator argument missing', '')

            content = template_params.pop('content')
            contents = []
            template_env = SandboxedEnvironment(autoescape=True)
            for _application, modes in content.iteritems():
                for _mode, _content in modes.iteritems():
                    _content['mode'] = _mode
                    _content['application'] = _application
                    try:
                        template_env.from_string(_content['subject'])
                        template_env.from_string(_content['body'])
                    except jinja2.TemplateSyntaxError as e:
                        logger.exception('Invalid jinja syntax')
                        raise HTTPBadRequest('Invalid jinja template', str(e))
                    contents.append(_content)

            template_id = session.execute('''INSERT INTO `template` (`name`, `created`, `user_id`)
                                             VALUES (:name, now(), (SELECT `id` from `target` where `name` = :creator AND `type_id` = (
                                                        SELECT `id` FROM `target_type` WHERE `name` = 'user'
                                                      )))''', template_params).lastrowid

            for _content in contents:
                _content.update({'template_id': template_id})
                session.execute('''INSERT INTO `template_content` (`template_id`, `subject`, `body`, `application_id`, `mode_id`)
                                   VALUES (
                                     :template_id, :subject, :body,
                                     (SELECT `id` FROM `application` WHERE `name` = :application),
                                     (SELECT `id` FROM `mode` WHERE `name` = :mode)
                                   )''', _content)

            session.execute('''INSERT INTO `template_active` (`name`, `template_id`)
                               VALUES (:name, :template_id)
                               ON DUPLICATE KEY UPDATE `template_id`=:template_id''',
                            {'name': template_params['name'], 'template_id': template_id})
            session.commit()
            session.close()
        except HTTPBadRequest:
            raise
        except Exception:
            session.close()
            logger.exception('ERROR')
            raise

        resp.status = HTTP_201
        resp.set_header('Location', '/templates/%s' % template_id)
        resp.body = ujson.dumps(template_id)


class UserModes(object):
    allow_read_no_auth = False
    enforce_user = True

    def on_get(self, req, resp, username):
        session = db.Session()
        try:
            results = session.execute('SELECT `name` FROM `priority`')
            modes = {name: 'default' for (name, ) in results}

            app = req.get_param('application')
            if app is None:
                result = session.execute(get_user_modes_query, {'username': username})
            else:
                result = session.execute(get_target_application_modes_query, {'username': username, 'app': app})
            modes.update(list(result))

            session.close()
            resp.status = HTTP_200
            resp.body = ujson.dumps(modes)
        except Exception:
            session.close()
            logger.exception('ERROR')
            raise

    # TODO (dewang): change to PUT for consistency with oncall
    def on_post(self, req, resp, username):
        session = db.Session()
        mode_params = ujson.loads(req.context['body'])
        try:
            results = session.execute('SELECT `name` FROM `priority`')
            modes = {name: 'default' for (name, ) in results}

            app = mode_params.pop('application', None)
            multiple_apps = mode_params.pop('per_app_modes', None)

            # Configure priority -> mode for a single application
            if app is not None:
                for p, m in mode_params.iteritems():
                    if m != 'default':
                        session.execute(insert_target_application_modes_query,
                                        {'name': username, 'priority': p, 'mode': m, 'app': app})
                    else:
                        session.execute(delete_target_application_modes_query,
                                        {'name': username, 'priority': p, 'app': app})
                result = session.execute(get_target_application_modes_query, {'username': username, 'app': app})

            # Configure priority -> mode for multiple applications in one call (avoid MySQL deadlocks)
            elif multiple_apps is not None:
                for app, app_modes in multiple_apps.iteritems():
                    for p, m in app_modes.iteritems():
                        if m != 'default':
                            session.execute(insert_target_application_modes_query,
                                            {'name': username, 'priority': p, 'mode': m, 'app': app})
                        else:
                            session.execute(delete_target_application_modes_query,
                                            {'name': username, 'priority': p, 'app': app})

                # Also configure global defaults in the same call if they're specified
                for p in mode_params.viewkeys() & modes.viewkeys():
                    m = mode_params[p]
                    if m != 'default':
                        session.execute(insert_user_modes_query, {'name': username, 'priority': p, 'mode': m})
                    else:
                        session.execute(delete_user_modes_query, {'name': username, 'priority': p})
                result = session.execute(get_user_modes_query, {'username': username})

            # Configure user's global priority -> mode which covers all applications that don't have defaults set
            else:
                for p, m in mode_params.iteritems():
                    if m != 'default':
                        session.execute(insert_user_modes_query, {'name': username, 'priority': p, 'mode': m})
                    else:
                        session.execute(delete_user_modes_query, {'name': username, 'priority': p})
                result = session.execute(get_user_modes_query, {'username': username})

            modes.update(list(result))
            session.commit()
            session.close()
            resp.status = HTTP_200
            resp.body = ujson.dumps(modes)
        except Exception:
            session.close()
            logger.exception('ERROR')
            raise


class TargetRoles(object):
    allow_read_no_auth = True

    def on_get(self, req, resp):
        '''
        Target role fetch endpoint.

        **Example request**:

        .. sourcecode:: http

           GET /v0/target_roles HTTP/1.1

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           [
               {
                   "name": "user",
                   "type": "user"
               },
               {
                   "name": "oncall",
                   "type": "team"
               }
           ]
        '''
        session = db.Session()
        try:
            sql = '''SELECT `target_role`.`name` AS `name`, `target_type`.`name` AS `type`
                     FROM `target_role`
                     JOIN `target_type` on `target_role`.`type_id` = `target_type`.`id`'''
            results = session.execute(sql)
            payload = ujson.dumps([{'name': row[0], 'type': row[1]} for row in results])
            session.close()
            resp.status = HTTP_200
            resp.body = payload
        except Exception:
            session.close()
            logger.exception('ERROR')
            raise


class Targets(object):
    allow_read_no_auth = False

    def on_get(self, req, resp):
        session = db.Session()
        filters_sql = []
        try:
            if 'startswith' in req.params:
                req.params['startswith'] = req.params['startswith'] + '%'
                filters_sql.append('`name` like :startswith')

            sql = '''SELECT DISTINCT `name` FROM `target`'''

            if filters_sql:
                sql += ' WHERE %s' % ' AND '.join(filters_sql)

            results = session.execute(sql, req.params)

            payload = ujson.dumps([row for (row,) in results])
            session.close()
            resp.status = HTTP_200
            resp.body = payload
        except Exception:
            session.close()
            logger.exception('Failed getting targets')
            raise


class Target(object):
    allow_read_no_auth = False

    def on_get(self, req, resp, target_type):
        session = db.Session()
        filters_sql = []
        try:
            req.params['type_id'] = cache.target_types[target_type]
            filters_sql.append('`type_id` = :type_id')

            if 'startswith' in req.params:
                req.params['startswith'] = req.params['startswith'] + '%'
                filters_sql.append('`name` like :startswith')

            sql = '''SELECT `name` FROM `target`'''

            if filters_sql:
                sql += ' WHERE %s' % ' AND '.join(filters_sql)

            results = session.execute(sql, req.params)

            payload = ujson.dumps([row for (row,) in results])
            session.close()
            resp.status = HTTP_200
            resp.body = payload
        except Exception:
            session.close()
            logger.exception('ERROR')
            raise


class Application(object):
    allow_read_no_auth = True

    def on_get(self, req, resp, app_name):
        connection = db.engine.raw_connection()
        cursor = connection.cursor(db.dict_cursor)
        app_query = get_applications_query + " AND `application`.`name` = %s"
        cursor.execute(app_query, app_name)
        app = cursor.fetchone()
        if not app:
            cursor.close()
            connection.close()
            raise HTTPBadRequest('Application %s not found' % app_name, '')

        cursor.execute(get_vars_query, app['id'])
        app['variables'] = []
        app['required_variables'] = []
        for row in cursor:
            app['variables'].append(row['name'])
            if row['required']:
                app['required_variables'].append(row['name'])

        cursor.execute(get_default_application_modes_query, app_name)
        app['default_modes'] = {row['priority']: row['mode'] for row in cursor}

        cursor.execute(get_supported_application_modes_query, app['id'])
        app['supported_modes'] = [row['name'] for row in cursor]

        cursor.execute(get_application_owners_query, app['id'])
        app['owners'] = [row['name'] for row in cursor]

        cursor.close()
        connection.close()

        del app['id']
        payload = app
        resp.status = HTTP_200
        resp.body = ujson.dumps(payload)

    def on_put(self, req, resp, app_name):
        try:
            data = ujson.loads(req.context['body'])
        except ValueError:
            raise HTTPBadRequest('Invalid json in post body', '')

        session = db.Session()

        app = session.execute(get_applications_query + ' AND `application`.`name` = :app_name', {'app_name': app_name}).fetchone()
        if not app:
            session.close()
            raise HTTPBadRequest('Application %s not found' % app_name, '')

        # Only admins and application owners can change app settings
        is_owner = bool(session.execute(check_application_ownership_query, {'application_id': app['id'], 'username': req.context['username']}).scalar())
        if not is_owner and not req.context['is_admin']:
            session.close()
            raise HTTPUnauthorized('Only admins and app owners can change this app\'s settings.', '')

        try:
            ujson.loads(data['sample_context'])
        except (KeyError, ValueError):
            raise HTTPBadRequest('sample_context must be valid json', '')

        if 'context_template' not in data:
            raise HTTPBadRequest('context_template must be specified', '')

        if 'summary_template' not in data:
            raise HTTPBadRequest('summary_template must be specified', '')

        new_variables = data.get('variables')
        if not isinstance(new_variables, list):
            raise HTTPBadRequest('variables must be specified and be a list', '')
        new_variables = set(new_variables)

        existing_variables = {row[0] for row in session.execute('SELECT `name` FROM `template_variable` WHERE `application_id` = :application_id',
                                                                {'application_id': app['id']})}

        kill_variables = existing_variables - new_variables

        for variable in new_variables - existing_variables:
            session.execute('INSERT INTO `template_variable` (`application_id`, `name`) VALUES (:application_id, :variable)',
                            {'application_id': app['id'], 'variable': variable})

        if kill_variables:
            session.execute('DELETE FROM `template_variable` WHERE `application_id` = :application_id AND `name` IN :variables',
                            {'application_id': app['id'], 'variables': tuple(kill_variables)})

        # Only owners can (optionally) change owners
        new_owners = data.get('owners')
        if new_owners is not None:
            if not isinstance(new_owners, list):
                raise HTTPBadRequest('To change owners, you must pass a list of strings', '')

            new_owners = set(new_owners)

            # Make it impossible for the current user to remove themselves as an owner, unless they're an admin
            if is_owner and not req.context['is_admin']:
                new_owners.add(req.context['username'])

            existing_owners = {row[0] for row in session.execute('''SELECT `target`.`name`
                                                                    FROM `target`
                                                                    JOIN `application_owner` ON `target`.`id` = `application_owner`.`user_id`
                                                                    WHERE `application_owner`.`application_id` = :application_id''', {'application_id': app['id']})}
            kill_owners = existing_owners - new_owners
            add_owners = new_owners - existing_owners

            for owner in add_owners:
                try:
                    session.execute('''INSERT INTO `application_owner` (`application_id`, `user_id`)
                                       VALUES (:application_id, (SELECT `user`.`target_id` FROM `user`
                                                                 JOIN `target` on `target`.`id` = `user`.`target_id`
                                                                 WHERE `target`.`name` = :owner))''', {'application_id': app['id'], 'owner': owner})
                except IntegrityError:
                    logger.exception('Integrity error whilst adding user %s as an owner to app %s', owner, app_name)

            if kill_owners:
                session.execute('''DELETE FROM `application_owner`
                                   WHERE `application_id` = :application_id
                                   AND `user_id` IN (SELECT `user`.`target_id` FROM `user`
                                                     JOIN `target` on `target`.`id` = `user`.`target_id`
                                                     WHERE `target`.`name` IN :owners)''', {'application_id': app['id'], 'owners': tuple(kill_owners)})

            if kill_owners or add_owners:
                logger.info('User %s has changed owners for app %s to: %s', req.context['username'], app_name, ', '.join(new_owners))

        # Only admins can (optionally) change supported modes
        new_modes = data.get('supported_modes')
        if req.context['is_admin'] and new_modes is not None:
            if not isinstance(new_modes, list):
                raise HTTPBadRequest('To change modes, you must pass a list of strings', '')

            new_modes = set(new_modes)
            existing_modes = {row[0] for row in session.execute('''SELECT `mode`.`name`
                                                                   FROM `mode`
                                                                   JOIN `application_mode` ON `application_mode`.`mode_id` = `mode`.`id`
                                                                   WHERE `application_mode`.`application_id` = :application_id''', {'application_id': app['id']})}
            kill_modes = existing_modes - new_modes
            add_modes = new_modes - existing_modes

            for mode in add_modes:
                try:
                    session.execute('''INSERT INTO `application_mode` (`application_id`, `mode_id`)
                                       VALUES (:application_id, (SELECT `mode`.`id` FROM `mode`
                                                                 WHERE `mode`.`name` = :mode))''', {'application_id': app['id'], 'mode': mode})
                except IntegrityError:
                    logger.exception('Integrity error whilst adding  %s as an mode to app %s', mode, app_name)

            if kill_modes:
                session.execute('''DELETE FROM `application_mode`
                                   WHERE `application_id` = :application_id
                                   AND `mode_id` IN (SELECT `mode`.`id` FROM `mode`
                                                     WHERE `mode`.`name` IN :modes)''', {'application_id': app['id'], 'modes': tuple(kill_modes)})

                session.execute('''DELETE FROM `default_application_mode`
                                   WHERE `application_id` = :application_id
                                   AND `mode_id` IN (SELECT `mode`.`id` FROM `mode`
                                                     WHERE `mode`.`name` IN :modes)''', {'application_id': app['id'], 'modes': tuple(kill_modes)})
            session.commit()

            if kill_modes or add_modes:
                logger.info('User %s has changed supported_modes for app %s to: %s', req.context['username'], app_name, ', '.join(new_modes))

        # Also support changing the default modes per priority per app, adhering to ones that are allowed for said app.
        default_modes = data.get('default_modes')
        if isinstance(default_modes, dict):
            existing_priorities = {row[0] for row in session.execute('''SELECT `priority`.`name`
                                                                        FROM `default_application_mode`
                                                                        JOIN `priority` on `priority`.`id` = `default_application_mode`.`priority_id`
                                                                        WHERE `default_application_mode`.`application_id` = :application_id''', {'application_id': app['id']})}
            kill_priorities = existing_priorities - default_modes.viewkeys()
            for priority, mode in default_modes.iteritems():

                # If we disabled this mode for this app in the code block above, avoid the expected integrity error here by bailing early
                if new_modes is not None and mode not in new_modes:
                    logger.warn('Not setting default priority %s to mode %s for app %s as this mode was disabled as part of this app update', priority, mode, app_name)
                    continue

                try:
                    session.execute('''INSERT INTO `default_application_mode` (`application_id`, `priority_id`, `mode_id`)
                                       VALUES (:application_id, (SELECT `id` FROM `priority` WHERE `name` = :priority),
                                               (SELECT `id` FROM `mode`
                                                JOIN `application_mode` ON `application_mode`.`application_id` = :application_id
                                                AND `application_mode`.`mode_id` = `mode`.`id`
                                                WHERE `mode`.`name` = :mode))
                                       ON DUPLICATE KEY UPDATE `mode_id` = (SELECT `id` FROM `mode`
                                                JOIN `application_mode` ON `application_mode`.`application_id` = :application_id
                                                AND `application_mode`.`mode_id` = `mode`.`id`
                                                WHERE `mode`.`name` = :mode)''', {'application_id': app['id'], 'priority': priority, 'mode': mode})
                    session.commit()
                except IntegrityError:
                    logger.exception('Integrity error whilst setting default priority %s to mod %s for app %s', priority, mode, app_name)

            if kill_priorities:
                session.execute('''DELETE FROM `default_application_mode` WHERE `application_id` = :application_id
                                   AND `priority_id` IN ( SELECT `id` FROM `priority`  WHERE `name` in :priorities) ''', {'application_id': app['id'], 'priorities': tuple(kill_priorities)})

        data['application_id'] = app['id']

        session.execute('''UPDATE `application`
                          SET `context_template` = :context_template, `summary_template` = :summary_template,
                              `sample_context` = :sample_context
                          WHERE `id` = :application_id LIMIT 1''', data)

        session.commit()
        session.close()

        resp.body = '{}'

    def on_delete(self, req, resp, app_name):
        if not req.context['is_admin']:
            raise HTTPUnauthorized('Only admins can remove apps', '')

        session = db.Session()

        try:
            affected = session.execute('''DELETE FROM `application` WHERE `name` = :app_name''', {'app_name': app_name}).rowcount
            session.commit()
        except IntegrityError:
            raise HTTPBadRequest('Cannot remove app. It has likely already in use.', '')
        finally:
            session.close()

        if not affected:
            raise HTTPBadRequest('No rows changed; app name probably already deleted', '')

        resp.body = '[]'


class ApplicationQuota(object):
    allow_read_no_auth = True

    def on_get(self, req, resp, app_name):
        connection = db.engine.raw_connection()
        cursor = connection.cursor(db.dict_cursor)
        quota_query = get_application_quotas_query + ' WHERE `application`.`name` = %s'
        cursor.execute(quota_query, app_name)
        quota = cursor.fetchone()
        cursor.close()
        connection.close()
        if quota:
            resp.body = ujson.dumps(quota)
        else:
            resp.body = '{}'

    def on_post(self, req, resp, app_name):

        try:
            data = ujson.loads(req.context['body'])
        except ValueError:
            raise HTTPBadRequest('Invalid json in post body', '')

        if data.viewkeys() != required_quota_keys:
            raise HTTPBadRequest('Missing required keys in post body', '')

        try:
            for key in quota_int_keys:
                if int(data[key]) < 1:
                    raise HTTPBadRequest('All int keys must be over 0', '')
        except ValueError:
            raise HTTPBadRequest('Some int keys are not integers', '')

        if data['hard_quota_threshold'] <= data['soft_quota_threshold']:
            raise HTTPBadRequest('Hard threshold must be bigger than soft threshold', '')

        session = db.Session()

        application_id = session.execute('SELECT `id` FROM `application` WHERE `name` = :app_name', {'app_name': app_name}).scalar()

        if not application_id:
            session.close()
            raise HTTPBadRequest('No ID found for that application', '')

        # Only admins and application owners can change quota settings
        if not req.context['is_admin']:
            if not session.execute(check_application_ownership_query, {'application_id': application_id, 'username': req.context['username']}).scalar():
                session.close()
                raise HTTPUnauthorized('You don\'t have permissions to update this app\'s quota.', '')

        if not session.execute('SELECT 1 FROM `plan_active` WHERE `name` = :plan_name', data).scalar():
            session.close()
            raise HTTPBadRequest('No active ID found for that plan', '')

        target_id = session.execute('SELECT `id` FROM `target` WHERE `name` = :target_name', data).scalar()

        if not target_id:
            session.close()
            raise HTTPBadRequest('No ID found for that target', '')

        data['application_id'] = application_id
        data['target_id'] = target_id

        session.execute(insert_application_quota_query, data)
        session.commit()
        session.close()

        resp.status = HTTP_201
        resp.body = '{}'

    def on_delete(self, req, resp, app_name):
        session = db.Session()

        application_id = session.execute('SELECT `id` FROM `application` WHERE `name` = :app_name', {'app_name': app_name}).scalar()

        if not application_id:
            session.close()
            raise HTTPBadRequest('No ID found for that application', '')

        if not req.context['is_admin']:
            if not session.execute(check_application_ownership_query, {'application_id': application_id, 'username': req.context['username']}).scalar():
                session.close()
                raise HTTPUnauthorized('You don\'t have permissions to update this app\'s quota.', '')

        session.execute('DELETE FROM `application_quota` WHERE `application_id` = :application_id', {'application_id': application_id})
        session.commit()
        session.close()

        resp.status = HTTP_204
        resp.body = '{}'


class ApplicationKey(object):
    allow_read_no_auth = False

    def on_get(self, req, resp, app_name):
        if not req.context['username']:
            raise HTTPUnauthorized('You must be a logged in user to view this app\'s key', '')

        session = db.Session()

        if not req.context['is_admin']:
            if not session.execute('''SELECT 1
                                      FROM `application_owner`
                                      JOIN `target` on `target`.`id` = `application_owner`.`user_id`
                                      JOIN `application` on `application`.`id` = `application_owner`.`application_id`
                                      WHERE `target`.`name` = :username
                                      AND `application`.`name` = :app_name''', {'app_name': app_name, 'username': req.context['username']}).scalar():
                session.close()
                raise HTTPForbidden('You don\'t have permissions to view this app\'s key.', '')

        key = session.execute('''SELECT `key` FROM `application` WHERE `name` = :app_name LIMIT 1''', {'app_name': app_name}).scalar()

        if not key:
            session.close()
            raise HTTPBadRequest('Key for this application not found', '')

        session.close()

        resp.body = ujson.dumps({'key': key})


class ApplicationReKey(object):
    allow_read_no_auth = False

    def on_post(self, req, resp, app_name):
        if not req.context['is_admin']:
            raise HTTPUnauthorized('You must be an admin to rekey an app', '')

        data = {
            'app_name': app_name,
            'new_key': hashlib.sha256(os.urandom(32)).hexdigest()
        }

        session = db.Session()
        affected = session.execute('''UPDATE `application` SET `key` = :new_key WHERE `name` = :app_name''', data).rowcount
        session.commit()
        session.close()

        if not affected:
            raise HTTPBadRequest('No rows changed; app name likely incorrect', '')

        logger.info('Admin user %s has re-key\'d app %s', req.context['username'], app_name)

        resp.body = '[]'


class ApplicationEmailIncidents(object):
    allow_read_no_auth = False

    def on_get(self, req, resp, app_name):
        '''
        Get email addresses which will create incidents on behalf of this application

        **Example request**:

        .. sourcecode:: http

           GET /v0/applications/{app_name}/incident_emails HTTP/1.1

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           {
             "incident@fakeemail.cde": "page_oncall_plan",
             "audit@fakeemail.abc": "audit_plan"
           }
        '''
        connection = db.engine.raw_connection()
        cursor = connection.cursor()
        cursor.execute('''SELECT `incident_emails`.`email`, `incident_emails`.`plan_name`
                          FROM `incident_emails`
                          JOIN `application` on `application`.`id` = `incident_emails`.`application_id`
                          WHERE `application`.`name` = %s''', app_name)

        payload = dict(cursor)
        cursor.close()
        connection.close()
        resp.body = ujson.dumps(payload)

    def on_put(self, req, resp, app_name):
        if not req.context['username']:
            raise HTTPUnauthorized('You must be a logged in user to change this application\'s email incident settings', '')

        session = db.Session()

        if not req.context['is_admin']:
            if not session.execute('''SELECT 1
                                      FROM `application_owner`
                                      JOIN `target` on `target`.`id` = `application_owner`.`user_id`
                                      JOIN `application` on `application`.`id` = `application_owner`.`application_id`
                                      WHERE `target`.`name` = :username
                                      AND `application`.`name` = :app_name''', {'app_name': app_name, 'username': req.context['username']}).scalar():
                session.close()
                raise HTTPForbidden('You don\'t have permissions to change this application\'s email incident settings.', '')

        try:
            email_to_plans = ujson.loads(req.context['body'])
        except ValueError:
            raise HTTPBadRequest('Invalid json in post body')

        if email_to_plans:
            email_addresses = tuple(email_to_plans.keys())

            # If we're trying to configure email addresses which are members contacts, block this
            check_users_emails = session.execute('''SELECT `target_contact`.`destination`
                                                    FROM `target_contact`
                                                    WHERE `target_contact`.`destination` IN :email_addresses
                                                    ''', {'email_addresses': email_addresses}).fetchall()
            if check_users_emails:
                session.close()
                raise HTTPBadRequest('These email addresses are also user\'s email addresses which is not allowed: %s' % ', '.join(row[0] for row in check_users_emails))

            # If we're trying to configure email addresses currently in use by other apps, block this
            check_other_apps_emails = session.execute('''SELECT `incident_emails`.`email`
                                                         FROM `incident_emails`
                                                         WHERE `incident_emails`.`application_id` != (SELECT `id` FROM `application` WHERE `name` = :app_name)
                                                         AND `incident_emails`.`email` in :email_addresses''', {'app_name': app_name, 'email_addresses': email_addresses}).fetchall()
            if check_other_apps_emails:
                session.close()
                raise HTTPBadRequest('These email addresses are already in use by another app: %s' % ', '.join(row[0] for row in check_other_apps_emails))

            # Delete all email -> plan configurations which are not present in this, for this app
            session.execute('''DELETE FROM `incident_emails`
                               WHERE `incident_emails`.`application_id` = (SELECT `id` FROM `application` WHERE `name` = :app_name)
                               AND `incident_emails`.`email` NOT IN :email_addresses''', {'app_name': app_name, 'email_addresses': email_addresses})

            # Configure new/existing ones
            for email_address, plan_name in email_to_plans.iteritems():

                # If this plan does not have steps that support this app, block this
                app_template_count = session.execute('''
                    SELECT EXISTS (
                        SELECT 1 FROM
                        `plan_notification`
                        JOIN `template` ON `template`.`name` = `plan_notification`.`template`
                        JOIN `template_content` ON `template_content`.`template_id` = `template`.`id`
                        WHERE `plan_notification`.`plan_id` = (SELECT `plan_id` FROM `plan_active` WHERE `name` = :plan_name)
                        AND `template_content`.`application_id` = (SELECT `id` FROM `application` WHERE `name` = :app_name)
                    )
                ''', {'app_name': app_name, 'plan_name': plan_name}).scalar()

                if not app_template_count:
                    session.close()
                    raise HTTPBadRequest('Failed adding %s -> %s combination. This plan does not have any templates which support this app.' % (email_address, plan_name))

                try:
                    session.execute('''INSERT INTO `incident_emails` (`application_id`, `email`, `plan_name`)
                                       VALUES ((SELECT `id` FROM `application` WHERE `name` = :app_name), :email_address, :plan_name)
                                       ON DUPLICATE KEY UPDATE `plan_name` = :plan_name ''', {'app_name': app_name, 'email_address': email_address, 'plan_name': plan_name})
                except IntegrityError:
                    session.close()
                    raise HTTPBadRequest('Failed adding %s -> %s combination. Is your plan name correct?' % (email_address, plan_name))
        else:
            session.execute('''DELETE FROM `incident_emails` WHERE `application_id` = (SELECT `id` FROM `application` WHERE `name` = :app_name)''', {'app_name': app_name})

        session.commit()
        session.close()

        resp.body = '[]'
        resp.status = HTTP_200


class ApplicationRename(object):
    allow_read_no_auth = False

    def on_put(self, req, resp, app_name):
        if not req.context['is_admin']:
            raise HTTPUnauthorized('Only admins can rename apps', '')

        try:
            data = ujson.loads(req.context['body'])
        except ValueError:
            raise HTTPBadRequest('Invalid json in post body', '')

        new_name = data.get('new_name', '').strip()

        if new_name == '':
            raise HTTPBadRequest('Missing new_name from post body', '')

        if new_name == app_name:
            raise HTTPBadRequest('New and old app name are identical', '')

        session = db.Session()

        data = {
            'new_name': new_name,
            'old_name': app_name
        }

        try:
            affected = session.execute('''UPDATE `application` SET `name` = :new_name WHERE `name` = :old_name''', data).rowcount
            session.commit()
        except IntegrityError:
            raise HTTPBadRequest('Destination app name likely already exists', '')
        finally:
            session.close()

        if not affected:
            raise HTTPBadRequest('No rows changed; old app name incorrect', '')

        resp.body = '[]'


class ApplicationPlans(object):
    allow_read_no_auth = True

    def on_get(self, req, resp, app_name):
        '''
        Search endpoint for active plans that support a given app.
        A plan supports an app if one of its steps uses a template
        that defines content for that application.

        **Example request**:

        .. sourcecode:: http

           GET /v0/applications/app-foo/plans?name__contains=bar& HTTP/1.1

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           [
               {
                   "description": "This is plan bar",
                   "threshold_count": 10,
                   "creator": "user1",
                   "created": 1478154275,
                   "aggregation_reset": 300,
                   "aggregation_window": 300,
                   "threshold_window": 900,
                   "tracking_type": null,
                   "tracking_template": null,
                   "tracking_key": null,
                   "active": 1,
                   "id": 123456,
                   "name": "bar-sla0"
               }
           ]
        '''
        fields = req.get_param_as_list('fields')
        fields = [f for f in fields if f in plan_columns] if fields else None
        req.params.pop('fields', None)
        if not fields:
            fields = plan_columns.keys()

        connection = db.engine.raw_connection()
        cursor = connection.cursor(db.dict_cursor)
        where = ['`application`.`name` = %s']
        where += gen_where_filter_clause(
            connection, plan_filters, plan_filter_types, req.params)

        query = '''SELECT %s
                   FROM `plan_active` JOIN `plan` ON `plan_active`.`plan_id` = `plan`.`id`
                   JOIN `plan_notification` ON `plan`.`id` = `plan_notification`.`plan_id`
                   JOIN `template` ON `plan_notification`.`template` = `template`.`name`
                   JOIN `template_active` ON `template`.`id` = `template_active`.`template_id`
                   JOIN `template_content` ON `template`.`id` = `template_content`.`template_id`
                   JOIN `application` ON `template_content`.`application_id` = `application`.`id`
                   JOIN `target` ON `target`.`id` = `plan`.`user_id`
                   WHERE %s
                   GROUP BY `plan`.`id`''' % (','.join(plan_columns[f] for f in fields if f in plan_columns),
                                              ' AND '.join(where))

        cursor.execute(query, app_name)
        resp.body = ujson.dumps(cursor)
        cursor.close()
        connection.close()


class Applications(object):
    allow_read_no_auth = True

    def on_get(self, req, resp):
        connection = db.engine.raw_connection()
        cursor = connection.cursor(db.dict_cursor)
        cursor.execute(get_applications_query)
        apps = cursor.fetchall()
        for app in apps:
            cursor.execute(get_vars_query, app['id'])
            app['variables'] = []
            app['required_variables'] = []
            for row in cursor:
                app['variables'].append(row['name'])
                if row['required']:
                    app['required_variables'].append(row['name'])

            cursor.execute(get_default_application_modes_query, app['name'])
            app['default_modes'] = {row['priority']: row['mode'] for row in cursor}

            cursor.execute(get_supported_application_modes_query, app['id'])
            app['supported_modes'] = [row['name'] for row in cursor]

            cursor.execute(get_application_owners_query, app['id'])
            app['owners'] = [row['name'] for row in cursor]

            del app['id']
        payload = apps
        cursor.close()
        connection.close()
        resp.status = HTTP_200
        resp.body = ujson.dumps(payload)

    def on_post(self, req, resp):
        try:
            data = ujson.loads(req.context['body'])
        except ValueError:
            raise HTTPBadRequest('Invalid json in post body', '')

        app_name = data.get('name', '').strip()

        if app_name == '':
            raise HTTPBadRequest('Missing app name', '')

        # Only iris super admins can create apps
        if not req.context['is_admin']:
            raise HTTPUnauthorized('Only admins can create apps', '')

        new_app_data = {
            'name': app_name,
            'key': hashlib.sha256(os.urandom(32)).hexdigest()
        }

        session = db.Session()

        try:
            app_id = session.execute('''INSERT INTO `application` (`name`, `key`) VALUES (:name, :key)''', new_app_data).lastrowid
            session.commit()
        except IntegrityError:
            session.close()
            raise HTTPBadRequest('This app already exists', '')

        # Enable all modes for this app except for "drop" by default
        try:
            session.execute('''INSERT INTO `application_mode` (`application_id`, `mode_id`)
                               SELECT :app_id, `mode`.`id` FROM `mode` WHERE `mode`.`name` != 'drop' ''', {'app_id': app_id})
            session.commit()
        except IntegrityError:
            logger.error('Failed configuring supported modes for newly created app %s', app_name)
        finally:
            session.close()

        logger.info('Created application "%s" with id %s', app_name, app_id)

        resp.status = HTTP_201
        resp.body = ujson.dumps({'id': app_id})


class Modes(object):
    allow_read_no_auth = False

    def on_get(self, req, resp):
        '''
        List all iris modes

        **Example request**:

        .. sourcecode:: http

           GET /v0/modes HTTP/1.1

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           ["sms", "email", "slack", "call"]
        '''
        connection = db.engine.raw_connection()
        cursor = connection.cursor()
        # Deliberately omit "drop" as it's a special case only supported in very limited circumstances and shouldn't
        # be thrown all over the UI
        mode_query = 'SELECT `name` FROM `mode` WHERE `name` != "drop"'
        cursor.execute(mode_query)
        payload = [r[0] for r in cursor]
        cursor.close()
        connection.close()
        resp.status = HTTP_200
        resp.body = ujson.dumps(payload)


class Priorities(object):
    allow_read_no_auth = False

    def on_get(self, req, resp):
        connection = db.engine.raw_connection()
        cursor = connection.cursor(db.dict_cursor)
        mode_query = ''' SELECT `priority`.`id`, `priority`.`name` AS `name`, `mode`.`name` AS `default_mode`
                         FROM `priority` JOIN `mode` ON `priority`.`mode_id` = `mode`.`id`'''
        mode_query += ' ORDER BY `priority`.`id` ASC'

        cursor.execute(mode_query)
        payload = ujson.dumps([{'name': r['name'], 'default_mode': r['default_mode']} for r in cursor])
        cursor.close()
        connection.close()
        resp.status = HTTP_200
        resp.body = payload


class User(object):
    allow_read_no_auth = False
    enforce_user = True

    def on_get(self, req, resp, username):
        connection = db.engine.raw_connection()
        cursor = connection.cursor(db.dict_cursor)
        # Get user id/name
        user_query = '''SELECT `target`.`id`, `target`.`name`, `user`.`admin`
                        FROM `target`
                        JOIN `user` on `user`.`target_id` = `target`.`id`'''
        if username.isdigit():
            user_query += ' WHERE `target`.`id` = %s'
        else:
            user_query += ' WHERE `target`.`name` = %s'
        cursor.execute(user_query, username)
        if cursor.rowcount != 1:
            raise HTTPNotFound()
        user_data = cursor.fetchone()
        user_data['admin'] = bool(user_data['admin'])
        user_id = user_data.pop('id')

        # Get user contact modes
        modes_query = '''SELECT `priority`.`name` AS priority, `mode`.`name` AS `mode`
                         FROM `target` JOIN `target_mode` ON `target`.`id` = `target_mode`.`target_id`
                             JOIN `priority` ON `priority`.`id` = `target_mode`.`priority_id`
                             JOIN `mode` ON `mode`.`id` = `target_mode`.`mode_id`
                         WHERE `target`.`id` = %s'''
        cursor.execute(modes_query, user_id)
        user_data['modes'] = {}
        for row in cursor:
            user_data['modes'][row['priority']] = row['mode']

        # Get user contact modes per app
        user_data['per_app_modes'] = defaultdict(dict)
        cursor.execute(get_all_users_app_modes_query, user_id)
        for row in cursor:
            user_data['per_app_modes'][row['application']][row['priority']] = row['mode']

        # Get user teams
        teams_query = '''SELECT `target`.`name` AS `team`
                        FROM `user_team` JOIN `target` ON `user_team`.`team_id` = `target`.`id`
                        WHERE `user_team`.`user_id` = %s'''
        cursor.execute(teams_query, user_id)
        user_data['teams'] = []
        for row in cursor:
            user_data['teams'].append(row['team'])

        # Get user contact info
        contacts_query = '''SELECT `mode`.`name` AS `mode`, `target_contact`.`destination` AS `destination`
                            FROM `target_contact` JOIN `mode` ON `target_contact`.`mode_id` = `mode`.`id`
                            WHERE `target_contact`.`target_id` = %s'''
        cursor.execute(contacts_query, user_id)
        user_data['contacts'] = {}
        for row in cursor:
            user_data['contacts'][row['mode']] = row['destination']
        cursor.close()
        connection.close()
        resp.status = HTTP_200
        resp.body = ujson.dumps(user_data)


class ResponseMixin(object):
    allow_read_no_auth = False

    def __init__(self, iris_sender_app):
        self.iris_sender_app = iris_sender_app

    def create_response(self, msg_id, source, content):
        """
        Return the result of the insert
        """
        session = db.Session()
        try:
            response_dict = {
                'source': source,
                'message_id': msg_id,
                'content': content,
            }
            result = session.execute('''
              INSERT INTO `response` (`source`, `message_id`, `content`, `created`)
              VALUES (:source, :message_id, :content, now())
            ''', response_dict)
            session.commit()
            session.close()
            return result
        except Exception as e:
            session.close()
            logger.exception('Failed to create response', e)
            raise

    def create_email_message(self, application, dest, subject, body):
        if application not in cache.applications:
            return False, 'Application "%s" not found in %s.' % (application, cache.applications.keys())

        app = cache.applications[application]

        session = db.Session()
        try:

            sql = '''SELECT `target`.`id` FROM `target`
                     JOIN `target_contact` on `target_contact`.`target_id` = `target`.`id`
                     JOIN `mode` on `mode`.`id` = `target_contact`.`mode_id`
                     WHERE `mode`.`name` = 'email' AND `target_contact`.`destination` = :destination'''
            target_id = session.execute(sql, {'destination': dest}).scalar()
            if not target_id:
                session.close()
                msg = 'Failed to lookup target from destination: %s' % dest
                logger.warn(msg)
                raise HTTPBadRequest('Invalid request', msg)

            data = {
                'created': datetime.datetime.utcnow(),
                'application_id': app['id'],
                'subject': subject,
                'target_id': target_id,
                'body': body,
                'destination': dest
            }

            sql = '''INSERT INTO `message` (`created`, `application_id`, `subject`, `target_id`, `body`, `destination`, `mode_id`, `priority_id`)
                     VALUES (:created, :application_id, :subject, :target_id, :body, :destination,
                      (SELECT `id` FROM `mode` WHERE `name` = 'email'),
                      (SELECT `id` FROM `priority` WHERE `name` = 'low')
                     )'''
            message_id = session.execute(sql, data).lastrowid

            session.commit()
            session.close()
            return True, message_id
        except Exception:
            session.close()
            logger.exception('ERROR')
            raise

    def handle_user_response(self, mode, msg_id, source, content):
        '''
        Take action against the parsed user response form utils.parse_response().

        If the action involves claiming an incident (either one incident, or all
        using 'claim all'), run the appropriate plugin for that app on the user response,
        and update the user's response in the DB.

        Return the message generated by the plugin to the user, in the form of

        .. sourcecode::
            tuple (app_name, message_to_return)

        There are some special cases. If the msg_id is None and content is a string,
        that special string is returned to the user rather than any plugins being run.

        '''
        def validate_app(app):
            if not app:
                msg = "Invalid message({0}): no application found.".format(msg_id)
                logger.exception(msg)
                raise HTTPBadRequest(msg, msg)

        session = db.Session()
        is_batch = False
        is_claim_all = False
        if isinstance(msg_id, int) or (isinstance(msg_id, basestring) and msg_id.isdigit()):
            # FIXME: return error if message not found for id
            app = get_app_from_msg_id(session, msg_id)
            validate_app(app)
            self.create_response(msg_id, source, content)
        elif isinstance(msg_id, basestring) and uuid4hex.match(msg_id):
            # msg id is not pure digit, might be a batch id
            sql = 'SELECT message.id FROM message WHERE message.batch=:batch_id'
            results = session.execute(sql, {'batch_id': msg_id})
            mid_lst = [row[0] for row in results]
            if len(mid_lst) < 1:
                raise HTTPBadRequest('Invalid message id', 'invalid message id: %s' % msg_id)

            # assuming message batching is also keyed on app, so they are from
            # the same app
            app = get_app_from_msg_id(session, mid_lst[0])
            validate_app(app)
            for mid in mid_lst:
                self.create_response(mid, source, content)
            is_batch = True
        elif isinstance(msg_id, list) and content == 'claim_all':
            # Claim all functionality.
            if not msg_id:
                return self.iris_sender_app, 'No incidents to claim'
            is_claim_all = True
            apps_to_message = defaultdict(list)
            for mid in msg_id:
                msg_app = get_app_from_msg_id(session, mid)
                if msg_app not in apps_to_message:
                    validate_app(msg_app)
                self.create_response(mid, source, content)
                apps_to_message[msg_app].append(mid)

        # Case where we want to give back a custom message as there was nothing to claim
        elif msg_id is None and isinstance(content, basestring):
            return '', content
        else:
            raise HTTPBadRequest('Invalid message id', 'invalid message id: %s' % msg_id)
        session.close()

        # Handle claim all differently as we might have messages from different applications
        if is_claim_all:
            try:
                plugin_output = {app: find_plugin(app).handle_response(mode, msg_ids, source, content, batch=is_batch)
                                 for app, msg_ids in apps_to_message.iteritems()}
            except Exception as e:
                logger.exception('Failed to handle %s response for mode %s for apps %s during claim all', content, mode, apps_to_message.keys())
                raise HTTPBadRequest('Failed to handle response', 'failed to handle response: %s' % str(e))

            if len(plugin_output) > 1:
                return plugin_output, '\n'.join('%s: %s' % (app, output) for app, output in plugin_output.iteritems())
            else:
                return plugin_output, '\n'.join(plugin_output.itervalues())

        else:
            try:
                resp = find_plugin(app).handle_response(
                    mode, msg_id, source, content, batch=is_batch)
            except Exception as e:
                logger.exception('Failed to handle %s response for mode %s for app %s', content, mode, app)
                raise HTTPBadRequest('Failed to handle response', 'failed to handle response: %s' % str(e))
            return app, resp


class ResponseGmail(ResponseMixin):
    def on_post(self, req, resp):
        gmail_params = ujson.loads(req.context['body'])
        email_headers = {header['name']: header['value'] for header in gmail_params['headers']}
        subject = email_headers.get('Subject')
        source = email_headers.get('From')
        if not source:
            msg = 'No source found in headers: %s' % gmail_params['headers']
            raise HTTPBadRequest('Missing source', msg)
        to = email_headers.get('To')
        # source is in the format of "First Last <user@email.com>",
        # but we only want the email part
        source = source.split(' ')[-1].strip('<>')
        content = gmail_params['body'].strip()

        # Some people want to use emails to create iris incidents. Facilitate this.
        if to:
            to = to.split(' ')[-1].strip('<>')
            session = db.Session()
            email_check_result = session.execute('''SELECT `incident_emails`.`application_id`, `plan_active`.`plan_id`
                                                    FROM `incident_emails`
                                                    JOIN `plan_active` ON `plan_active`.`name` = `incident_emails`.`plan_name`
                                                    WHERE `email` = :email
                                                    AND `email` NOT IN (SELECT `destination` FROM `target_contact` WHERE `mode_id` = (SELECT `id` FROM `mode` WHERE `name` = 'email'))''', {'email': to}).fetchone()
            if email_check_result:

                if 'In-Reply-To' in email_headers:
                    logger.warning('Not creating incident for email %s as this is an email reply, rather than a fresh email.', to)
                    resp.status = HTTP_204
                    resp.set_header('X-IRIS-INCIDENT', 'Not created (email reply not fresh email)')
                    return

                app_template_count = session.execute('''
                    SELECT EXISTS (
                        SELECT 1 FROM
                        `plan_notification`
                        JOIN `template` ON `template`.`name` = `plan_notification`.`template`
                        JOIN `template_content` ON `template_content`.`template_id` = `template`.`id`
                        WHERE `plan_notification`.`plan_id` = :plan_id
                        AND `template_content`.`application_id` = :app_id
                    )
                ''', {'app_id': email_check_result['application_id'], 'plan_id': email_check_result['plan_id']}).scalar()

                if not app_template_count:
                    session.close()
                    logger.warning('Not creating incident for email %s as no template actions for this app.', to)
                    resp.status = HTTP_204
                    resp.set_header('X-IRIS-INCIDENT', 'Not created (no template actions for this app)')
                    return

                incident_info = {
                    'application_id': email_check_result['application_id'],
                    'created': datetime.datetime.utcnow(),
                    'plan_id': email_check_result['plan_id'],
                    'context': ujson.dumps({'body': content, 'email': to})
                }
                incident_id = session.execute('''INSERT INTO `incident` (`plan_id`, `created`, `context`, `current_step`, `active`, `application_id`)
                                                 VALUES (:plan_id, :created, :context, 0, TRUE, :application_id) ''', incident_info).lastrowid
                session.commit()
                session.close()
                resp.status = HTTP_204
                resp.set_header('X-IRIS-INCIDENT', incident_id)  # Pass the new incident id back through a header so we can test this
                return

            session.close()

        # only parse first line of email content for now
        first_line = content.split('\n', 1)[0].strip()
        try:
            msg_id, cmd = utils.parse_email_response(first_line, subject, source)
        except (ValueError, IndexError):
            raise HTTPBadRequest('Invalid response', 'Invalid response: %s' % first_line)

        try:
            app, response = self.handle_user_response('email', msg_id, source, cmd)
        except Exception:
            logger.exception('Failed to handle email response: %s' % first_line)
            raise
        else:
            # When processing a claim all scenario, the first item returned by handle_user_response
            # will be a dict mapping the app to its plugin output.
            if isinstance(app, dict):
                for app_name, app_response in app.iteritems():
                    app_response = '%s: %s' % (app_name, app_response)
                    success, re = self.create_email_message(app_name, source, 'Re: %s' % subject, app_response)
                    if not success:
                        logger.error('Failed to send user response email: %s' % re)
                        raise HTTPBadRequest('Failed to send user response email', re)
            else:
                success, re = self.create_email_message(app, source, 'Re: %s' % subject, response)
                if not success:
                    logger.error('Failed to send user response email: %s' % re)
                    raise HTTPBadRequest('Failed to send user response email', re)
            resp.status = HTTP_204


class ResponseGmailOneClick(ResponseMixin):
    def on_post(self, req, resp):
        gmail_params = ujson.loads(req.context['body'])

        try:
            msg_id = int(gmail_params['msg_id'])
            email_address = gmail_params['email_address']
            cmd = gmail_params['cmd']
        except (ValueError, KeyError):
            raise HTTPBadRequest('Post body missing required key or key of wrong type', '')

        if cmd != 'claim':
            raise HTTPBadRequest('GmailOneClick only supports claiming individual messages', '')

        try:
            app, response = self.handle_user_response('email', msg_id, email_address, cmd)
        except Exception:
            logger.exception('Failed to handle gmail one click response: %s' % gmail_params)
            raise

        success, re = self.create_email_message(app, email_address, response, response)
        if not success:
            logger.error('Failed to send user response email: %s' % re)
            raise HTTPBadRequest('Failed to send user response email', re)
        resp.status = HTTP_204


class ResponseTwilioCalls(ResponseMixin):
    def on_post(self, req, resp):
        post_dict = parse_qs(req.context['body'])

        msg_id = req.get_param('message_id', required=True)
        if 'Digits' not in post_dict:
            raise HTTPBadRequest('Digits argument not found', '')
        # For phone call callbacks, To argument is the target and From is the
        # twilio number
        if 'To' not in post_dict:
            raise HTTPBadRequest('To argument not found', '')
        digits = post_dict['Digits'][0]
        source = post_dict['To'][0]

        try:
            _, response = self.handle_user_response('call', msg_id, source, digits)
        except Exception:
            logger.exception('Failed to handle call response: %s' % digits)
            raise
        else:
            resp.status = HTTP_200
            resp.body = ujson.dumps({'app_response': response})


class ResponseTwilioMessages(ResponseMixin):
    def on_post(self, req, resp):
        post_dict = parse_qs(req.context['body'])
        if 'Body' not in post_dict:
            raise HTTPBadRequest('SMS body not found', 'Missing Body argument in post body')

        if 'From' not in post_dict:
            raise HTTPBadRequest('From argument not found', 'Missing From in post body')
        source = post_dict['From'][0]
        body = post_dict['Body'][0]
        try:
            msg_id, content = utils.parse_response(body.strip(), 'sms', source)
        except (ValueError, IndexError):
            raise HTTPBadRequest('Invalid response', 'failed to parse response')

        try:
            _, response = self.handle_user_response('sms', msg_id, source, content)
        except Exception:
            logger.exception('Failed to handle sms response: %s' % body)
            raise
        else:
            resp.status = HTTP_200
            resp.body = ujson.dumps({'app_response': response})


class ResponseSlack(ResponseMixin):
    def on_post(self, req, resp):
        slack_params = ujson.loads(req.context['body'])
        try:
            msg_id = int(slack_params['msg_id'])
            source = slack_params['source']
            content = slack_params['content']
        except KeyError:
            raise HTTPBadRequest('Post body missing required key', '')
        try:
            _, response = self.handle_user_response('slack', msg_id, source, content)
        except Exception:
            logger.exception('Failed to handle slack response: %s' % req.context['body'])
            raise HTTPBadRequest('Bad Request', 'Failed to handle slack response')
        else:
            resp.status = HTTP_200
            resp.body = ujson.dumps({'app_response': response})


class TwilioDeliveryUpdate(object):
    allow_read_no_auth = False

    def on_post(self, req, resp):
        post_dict = falcon.uri.parse_query_string(req.context['body'])

        sid = post_dict.get('MessageSid', post_dict.get('CallSid'))
        status = post_dict.get('MessageStatus', post_dict.get('CallStatus'))

        if not sid or not status:
            logger.exception('Invalid twilio delivery update request. Payload: %s', post_dict)
            raise HTTPBadRequest('Invalid keys in payload', '')

        session = db.Session()
        affected = session.execute('''UPDATE `twilio_delivery_status`
                                      SET `status` = :status
                                      WHERE `twilio_sid` = :sid''', {'sid': sid, 'status': status}).rowcount
        session.commit()
        session.close()

        if not affected:
            logger.warn('No rows changed when updating delivery status for twilio sid: %s', sid)

        resp.status = HTTP_204


class Reprioritization(object):
    allow_read_no_auth = False
    enforce_user = True

    def on_get(self, req, resp, username):
        connection = db.engine.raw_connection()
        cursor = connection.cursor(db.dict_cursor)
        cursor.execute(reprioritization_setting_query, username)
        resp.body = ujson.dumps(cursor)
        cursor.close()
        connection.close()

    def on_post(self, req, resp, username):
        params = ujson.loads(req.context['body'])
        required_args = ['duration', 'count', 'src_mode', 'dst_mode']
        # Check for required arguments
        for arg in required_args:
            if arg not in params:
                raise HTTPBadRequest('Missing argument', 'missing arg: %s' % arg)

        # Validate duration/count
        try:
            duration = int(params['duration'])
        except ValueError:
            raise HTTPBadRequest('Invalid duration', 'duration must be an integer')
        if duration < 60:
            raise HTTPBadRequest('Invalid duration', 'duration must be greater than 1 minute')
        if duration > 3600:
            raise HTTPBadRequest('Invalid duration', 'duration must be at most 3600 seconds')
        try:
            count = int(params['count'])
        except ValueError:
            raise HTTPBadRequest('Invalid count', 'count must be an integer')
        if count <= 0:
            raise HTTPBadRequest('Invalid count', 'count must be greater than 0')
        if count > 255:
            raise HTTPBadRequest('Invalid count', 'count must be under 255')

        connection = db.engine.raw_connection()
        cursor = connection.cursor(db.dict_cursor)
        try:
            cursor.execute('SELECT `id` FROM `mode` WHERE `name` = %s', params['src_mode'])
            src_mode_id = cursor.fetchone()['id']
        except:
            msg = 'Invalid source mode.'
            logger.exception(msg)
            raise HTTPBadRequest(msg, msg)
        try:
            cursor.execute('SELECT `id` FROM `mode` WHERE `name` = %s', params['dst_mode'])
            dst_mode_id = cursor.fetchone()['id']
        except:
            msg = 'Invalid destination mode.'
            logger.exception(msg)
            raise HTTPBadRequest(msg, msg)
        cursor.close()

        session = db.Session()
        session.execute(update_reprioritization_settings_query, {
            'target': username,
            'src_mode_id': src_mode_id,
            'dst_mode_id': dst_mode_id,
            'count': count,
            'duration': duration,
        })
        session.commit()
        session.close()
        resp.status = HTTP_200
        resp.body = '[]'


class ReprioritizationMode(object):
    allow_read_no_auth = False
    enforce_user = True

    def on_delete(self, req, resp, username, src_mode_name):
        '''
        Delete a reprioritization mode for a user's mode setting

        **Example request**:

        .. sourcecode:: http

           DELETE /v0/users/reprioritization/{username}/{src_mode_name} HTTP/1.1

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           []
        '''
        session = db.Session()
        affected_rows = session.execute(delete_reprioritization_settings_query, {
            'target_name': username,
            'mode_name': src_mode_name,
        }).rowcount
        session.commit()
        session.close()

        if affected_rows == 0:
            raise HTTPNotFound()

        resp.status = HTTP_200
        resp.body = '[]'


class Healthcheck(object):
    allow_read_no_auth = True

    def __init__(self, path):
        self.healthcheck_path = path

    def on_get(self, req, resp):
        '''
        Healthcheck endpoint. Returns contents of healthcheck file.

        **Example request**:

        .. sourcecode:: http

           GET /v0/healthcheck HTTP/1.1

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: text/plain

           GOOD
        '''
        try:
            with open(self.healthcheck_path) as f:
                health = f.readline().strip()
        except:
            raise HTTPNotFound()
        resp.status = HTTP_200
        resp.content_type = 'text/plain'
        resp.body = health


class Stats(object):
    allow_read_no_auth = True

    def on_get(self, req, resp):
        queries = {
            'total_plans': 'SELECT COUNT(*) FROM `plan`',
            'total_incidents': 'SELECT COUNT(*) FROM `incident`',
            'total_messages_sent': 'SELECT COUNT(*) FROM `message`',
            'total_incidents_today': 'SELECT COUNT(*) FROM `incident` WHERE `created` >= CURDATE()',
            'total_messages_sent_today': 'SELECT COUNT(*) FROM `message` WHERE `sent` >= CURDATE()',
            'total_active_users': 'SELECT COUNT(*) FROM `target` WHERE `type_id` = (SELECT `id` FROM `target_type` WHERE `name` = "user") AND `active` = TRUE',
            'pct_incidents_claimed_last_month': '''SELECT ROUND(
                                                   (SELECT COUNT(*) FROM `incident`
                                                    WHERE `created` > (CURRENT_DATE - INTERVAL 29 DAY)
                                                    AND `created` < (CURRENT_DATE - INTERVAL 1 DAY)
                                                    AND `active` = FALSE
                                                    AND NOT isnull(`owner_id`)) /
                                                   (SELECT COUNT(*) FROM `incident`
                                                    WHERE `created` > (CURRENT_DATE - INTERVAL 29 DAY)
                                                    AND `created` < (CURRENT_DATE - INTERVAL 1 DAY)) * 100, 2)''',
            'median_seconds_to_claim_last_month': '''SELECT @incident_count := (SELECT count(*)
                                                                                FROM `incident`
                                                                                WHERE `created` > (CURRENT_DATE - INTERVAL 29 DAY)
                                                                                AND `created` < (CURRENT_DATE - INTERVAL 1 DAY)
                                                                                AND `active` = FALSE
                                                                                AND NOT ISNULL(`owner_id`)
                                                                                AND NOT ISNULL(`updated`)),
                                                            @row_id := 0,
                                                            (SELECT CEIL(AVG(time_to_claim)) as median
                                                            FROM (SELECT `updated` - `created` as time_to_claim
                                                                  FROM `incident`
                                                                  WHERE `created` > (CURRENT_DATE - INTERVAL 29 DAY)
                                                                  AND `created` < (CURRENT_DATE - INTERVAL 1 DAY)
                                                                  AND `active` = FALSE
                                                                  AND NOT ISNULL(`owner_id`)
                                                                  AND NOT ISNULL(`updated`)
                                                                  ORDER BY time_to_claim) as time_to_claim
                                                            WHERE (SELECT @row_id := @row_id + 1)
                                                            BETWEEN @incident_count/2.0 AND @incident_count/2.0 + 1)'''
        }

        stats = {}

        fields_filter = req.get_param_as_list('fields')
        fields = queries.viewkeys()
        if fields_filter:
            fields &= set(fields_filter)

        connection = db.engine.raw_connection()
        cursor = connection.cursor()
        for key in fields:
            start = time.time()
            cursor.execute(queries[key])
            result = cursor.fetchone()
            if result:
                result = result[-1]
            else:
                result = None
            logger.info('Stats query %s took %s seconds', key, round(time.time() - start, 2))
            stats[key] = result
        cursor.close()
        connection.close()

        resp.status = HTTP_200
        resp.body = ujson.dumps(stats)


class ApplicationStats(object):
    allow_read_no_auth = True

    def on_get(self, req, resp, app_name):
        app = cache.applications.get(app_name)
        if not app:
            raise HTTPNotFound()

        queries = {
            'total_incidents_today': 'SELECT COUNT(*) FROM `incident` WHERE `created` >= CURDATE() AND `application_id` = %(application_id)s',
            'total_messages_sent_today': 'SELECT COUNT(*) FROM `message` WHERE `sent` >= CURDATE() AND `application_id` = %(application_id)s',
            'total_incidents_last_month': 'SELECT COUNT(*) FROM `incident` WHERE `created` > (CURRENT_DATE - INTERVAL 29 DAY) AND `created` < (CURRENT_DATE - INTERVAL 1 DAY) AND `application_id` = %(application_id)s',
            'total_messages_sent_last_month': 'SELECT COUNT(*) FROM `message` WHERE `sent` > (CURRENT_DATE - INTERVAL 29 DAY) AND `sent` < (CURRENT_DATE - INTERVAL 1 DAY) AND `application_id` = %(application_id)s',
            'pct_incidents_claimed_last_month': '''SELECT ROUND(COUNT(`owner_id`) / COUNT(*) * 100, 2)
                                                   FROM `incident`
                                                   WHERE `created` > (CURRENT_DATE - INTERVAL 29 DAY)
                                                   AND `created` < (CURRENT_DATE - INTERVAL 1 DAY)
                                                   AND `application_id` = %(application_id)s''',
            'median_seconds_to_claim_last_month': '''SELECT @incident_count := (SELECT count(*)
                                                                                FROM `incident`
                                                                                WHERE `created` > (CURRENT_DATE - INTERVAL 29 DAY)
                                                                                AND `created` < (CURRENT_DATE - INTERVAL 1 DAY)
                                                                                AND `active` = FALSE
                                                                                AND NOT ISNULL(`owner_id`)
                                                                                AND NOT ISNULL(`updated`)
                                                                                AND `application_id` = %(application_id)s),
                                                            @row_id := 0,
                                                            (SELECT CEIL(AVG(time_to_claim)) as median
                                                            FROM (SELECT `updated` - `created` as time_to_claim
                                                                  FROM `incident`
                                                                  WHERE `created` > (CURRENT_DATE - INTERVAL 29 DAY)
                                                                  AND `created` < (CURRENT_DATE - INTERVAL 1 DAY)
                                                                  AND `active` = FALSE
                                                                  AND NOT ISNULL(`owner_id`)
                                                                  AND NOT ISNULL(`updated`)
                                                                  AND `application_id` = %(application_id)s
                                                                  ORDER BY time_to_claim) as time_to_claim
                                                            WHERE (SELECT @row_id := @row_id + 1)
                                                            BETWEEN @incident_count/2.0 AND @incident_count/2.0 + 1)''',
        }

        query_data = {'application_id': app['id']}

        stats = {}

        fields_filter = req.get_param_as_list('fields')
        fields = queries.viewkeys()
        if fields_filter:
            fields &= set(fields_filter)

        connection = db.engine.raw_connection()
        cursor = connection.cursor()
        for key in fields:
            start = time.time()
            cursor.execute(queries[key], query_data)
            result = cursor.fetchone()
            if result:
                result = result[-1]
            else:
                result = None
            logger.info('App Stats (%s) query %s took %s seconds', app['name'], key, round(time.time() - start, 2))
            stats[key] = result

        mode_status = defaultdict(lambda: defaultdict(int))

        mode_stats_types = {
            'sms': {
                'fail': ['undelivered'],
                'success': ['sent', 'delivered']
            },
            'call': {
                'success': ['completed'],
                'fail': ['failed']
            },
            'email': {
                'success': [1],
                'fail': [0],
            }
        }

        start = time.time()
        cursor.execute('''SELECT `mode`.`name`, COALESCE(`generic_message_sent_status`.`status`, `twilio_delivery_status`.`status`) as thisStatus,
                                  COUNT(*) FROM `message`
                          LEFT JOIN `twilio_delivery_status` on `twilio_delivery_status`.`message_id` = `message`.`id`
                          LEFT JOIN `generic_message_sent_status` on `generic_message_sent_status`.`message_id` = `message`.`id`
                          JOIN `mode` ON `mode`.`id` = `message`.`mode_id`
                          WHERE ((NOT ISNULL(`twilio_delivery_status`.`status`) AND `mode`.`name` != 'email') OR (NOT ISNULL(`generic_message_sent_status`.`status`) AND `mode`.`name` = 'email'))
                                AND `message`.`application_id` = %(application_id)s
                                AND `message`.`created` > (CURRENT_DATE - INTERVAL 29 DAY)
                                AND `message`.`created` < (CURRENT_DATE - INTERVAL 1 DAY)
                          GROUP BY thisStatus, `mode`.`name`''', query_data)
        logger.info('App Stats (%s) mode status query took %s seconds', app['name'], round(time.time() - start, 2))

        for mode, status, count in cursor:
            if isinstance(status, basestring) and status.isdigit():
                status = int(status)
            mode_status[mode][status] = count

        for mode in mode_stats_types:
            status_counts = mode_status[mode]
            overall = float(sum(status_counts.values()))
            if overall > 0:
                fail_pct = round((sum(status_counts.pop(key, 0) for key in mode_stats_types[mode]['fail']) / overall) * 100, 2)
                success_pct = round((sum(status_counts.pop(key, 0) for key in mode_stats_types[mode]['success']) / overall) * 100, 2)
                other_pct = round(sum(status_counts.values()) / overall * 100, 2)
            else:
                fail_pct = success_pct = other_pct = None
            stats['pct_%s_success_last_month' % mode] = success_pct
            stats['pct_%s_fail_last_month' % mode] = fail_pct
            stats['pct_%s_other_last_month' % mode] = other_pct

        cursor.close()
        connection.close()

        resp.status = HTTP_200
        resp.body = ujson.dumps(stats, sort_keys=True)


def update_cache_worker():
    while True:
        logger.debug('Reinitializing cache')
        cache.init()
        sleep(60)


def json_error_serializer(req, resp, exception):
    resp.body = exception.to_json()
    resp.content_type = 'application/json'


def construct_falcon_api(debug, healthcheck_path, allowed_origins, iris_sender_app, sender_addr):
    cors = CORS(allow_origins_list=allowed_origins)
    api = API(middleware=[
        ReqBodyMiddleware(),
        AuthMiddleware(debug=debug),
        ACLMiddleware(debug=debug),
        HeaderMiddleware(),
        cors.middleware
    ])

    api.set_error_serializer(json_error_serializer)

    api.add_route('/v0/plans/{plan_id}', Plan())
    api.add_route('/v0/plans', Plans())

    api.add_route('/v0/incidents/{incident_id}', Incident())
    api.add_route('/v0/incidents', Incidents())

    api.add_route('/v0/messages/{message_id}', Message())
    api.add_route('/v0/messages/{message_id}/auditlog', MessageAuditLog())
    api.add_route('/v0/messages', Messages())

    api.add_route('/v0/notifications', Notifications(sender_addr))

    api.add_route('/v0/targets/{target_type}', Target())
    api.add_route('/v0/targets', Targets())

    api.add_route('/v0/target_roles', TargetRoles())

    api.add_route('/v0/templates/{template_id}', Template())
    api.add_route('/v0/templates', Templates())

    api.add_route('/v0/users/{username}', User())
    api.add_route('/v0/users/modes/{username}', UserModes())
    api.add_route('/v0/users/reprioritization/{username}', Reprioritization())
    api.add_route('/v0/users/reprioritization/{username}/{src_mode_name}', ReprioritizationMode())

    api.add_route('/v0/modes', Modes())

    api.add_route('/v0/applications/{app_name}/quota', ApplicationQuota())
    api.add_route('/v0/applications/{app_name}/stats', ApplicationStats())
    api.add_route('/v0/applications/{app_name}/key', ApplicationKey())
    api.add_route('/v0/applications/{app_name}/rekey', ApplicationReKey())
    api.add_route('/v0/applications/{app_name}/incident_emails', ApplicationEmailIncidents())
    api.add_route('/v0/applications/{app_name}/rename', ApplicationRename())
    api.add_route('/v0/applications/{app_name}/plans', ApplicationPlans())
    api.add_route('/v0/applications/{app_name}', Application())
    api.add_route('/v0/applications', Applications())

    api.add_route('/v0/priorities', Priorities())

    api.add_route('/v0/response/gmail', ResponseGmail(iris_sender_app))
    api.add_route('/v0/response/gmail-oneclick', ResponseGmailOneClick(iris_sender_app))
    api.add_route('/v0/response/twilio/calls', ResponseTwilioCalls(iris_sender_app))
    api.add_route('/v0/response/twilio/messages', ResponseTwilioMessages(iris_sender_app))
    api.add_route('/v0/response/slack', ResponseSlack(iris_sender_app))
    api.add_route('/v0/twilio/deliveryupdate', TwilioDeliveryUpdate())

    api.add_route('/v0/stats', Stats())

    api.add_route('/healthcheck', Healthcheck(healthcheck_path))
    return api


def get_api(config):
    db.init(config)
    spawn(update_cache_worker)
    init_plugins(config.get('plugins', {}))
    init_validators(config.get('validators', []))
    healthcheck_path = config['healthcheck_path']
    allowed_origins = config.get('allowed_origins', [])
    iris_sender_app = config['sender'].get('sender_app')

    debug = False
    if config['server'].get('disable_auth'):
        debug = True
    master_sender = config['sender'].get('master_sender', config['sender'])
    master_sender_addr = (master_sender['host'], master_sender['port'])
    # all notifications go through master sender for now
    app = construct_falcon_api(
        debug, healthcheck_path, allowed_origins, iris_sender_app, master_sender_addr)

    # Need to call this after all routes have been created
    app = ui.init(config, app)
    return app


def get_api_app():
    logging.basicConfig(format='[%(asctime)s] [%(process)d] [%(levelname)s] %(name)s %(message)s',
                        level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S %z')
    return get_api(load_config())
