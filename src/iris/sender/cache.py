# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from collections import deque
import jinja2
from jinja2.sandbox import SandboxedEnvironment
from gevent import spawn, sleep
from gevent.pool import Pool
from .message import update_message_mode
from .. import db
from ..role_lookup import get_role_lookups
from . import auditlog

import logging
import ujson
logger = logging.getLogger(__name__)


plans = None
templates = None
incidents = None
roles = None
targets = None
plan_notifications = None
target_reprioritization = None
target_names = None
targets_for_role = None
dynamic_plan_map = None


class Cache():
    def __init__(self, engine, sql, active):
        self.engine = engine
        self.sql = sql
        self.active = active
        self.data = {}

    def __getitem__(self, key):
        try:
            return self.data[key]
        except KeyError:
            connection = self.engine.raw_connection()
            cursor = connection.cursor(db.dict_cursor)
            cursor.execute(self.sql, key)
            ret = self.data[key] = cursor.fetchone()
            cursor.close()
            connection.close()
            return ret

    def purge(self):
        if self.data and self.active:
            connection = self.engine.raw_connection()
            cursor = connection.cursor()
            cursor.execute(self.active, [tuple(self.data)])
            for key in self.data.keys() - {row[0] for row in cursor}:
                del self.data[key]
            cursor.close()
            connection.close()
        else:
            self.data = {}


class DynamicPlanMap(Cache):
    def __getitem__(self, key):
        try:
            return self.data[key]
        except KeyError:
            connection = self.engine.raw_connection()
            cursor = connection.cursor(db.dict_cursor)
            cursor.execute(self.sql, key)
            ret = self.data[key] = {row['dynamic_index']: row for row in cursor}
            cursor.close()
            connection.close()
            return ret


class Templates():
    def __init__(self, engine):
        # Autoescape needs to be False to avoid html-encoding ampersands in emails. This
        # does not create security vulns as on the frontend, html is escaped using Handlebars,
        # and in emails, html is allowed and ampersands are escaped with markdown's renderer.
        self.env = SandboxedEnvironment(autoescape=False)

        self.engine = engine
        self.active = {}
        self.data = {}

    def __getitem__(self, key):
        try:
            return self.data[key]
        except KeyError:
            template = {}
            connection = self.engine.raw_connection()
            cursor = connection.cursor()
            cursor.execute('''
                SELECT `template`.`id`, `application`.`name`, `mode`.`name`,
                       `template_content`.`subject`, `template_content`.`body`
                FROM `template_active`
                JOIN `template` ON `template`.`id` = `template_active`.`template_id`
                JOIN `template_content` ON `template_content`.`template_id` = `template_active`.`template_id`
                JOIN `application` ON `template_content`.`application_id` = `application`.`id`
                JOIN `mode` ON `template_content`.`mode_id` = `mode`.`id`
                WHERE `template_active`.`name` = %s''', key)

            for template_id, application, mode, subject, body in cursor:
                logger.debug('[+] adding template: %s %s %s %s', key, template_id, application, mode)
                try:
                    # make sure message_id is delivered to the user
                    if self.has_message_id(subject) or self.has_message_id(body):
                        subject = self.env.from_string(subject)
                    else:
                        if subject:
                            subject = self.env.from_string('{{ iris.message_id }} ' + subject)
                        else:
                            subject = self.env.from_string('{{ iris.message_id }}')
                    body = self.env.from_string(body)
                except jinja2.exceptions.TemplateSyntaxError:
                    logger.info('[-] error parsing template: %s %s %s %s', key, template_id, application, mode)
                    continue
                template['id'] = template_id
                template.setdefault(application, {})[mode] = {
                    'subject': subject,
                    'body': body
                }

            self.data[key] = template
            cursor.close()
            connection.close()
            return template

    def has_message_id(self, source):
        valid = False
        ast = self.env.parse(source)
        for node in ast.body:
            try:
                nodes = node.nodes
            except AttributeError:
                continue
            for n in nodes:
                try:
                    if n.node.name == 'iris':
                        try:
                            if n.arg.value == 'message_id':
                                valid = True
                        except AttributeError:
                            if n.attr == 'message_id':
                                valid = True
                except AttributeError:
                    continue
                if not valid:
                    break
            if not valid:
                break

        return valid

    def refresh(self):
        logger.info('refreshing templates')

        connection = self.engine.raw_connection()
        cursor = connection.cursor(db.dict_cursor)

        cursor.execute('''SELECT `template`.`id`, `template`.`name` FROM `template` INNER JOIN `template_active` ON `template`.`id` = `template_active`.`template_id`''')
        active = {row['id']: row['name'] for row in cursor}

        cursor.close()
        connection.close()

        new_active_ids = active.keys()
        old_active_ids = self.active.keys()

        old_ids = old_active_ids - new_active_ids
        new_ids = new_active_ids - old_active_ids

        for template_id in old_ids:
            try:
                del self.data[self.active[template_id]]
            except KeyError:
                logger.exception('Failed pruning old template_id %s', template_id)

        Pool(30).map(self.__getitem__, (active[id] for id in new_ids))

        self.active = active


class Plans():
    def __init__(self, engine):
        self.engine = engine
        self.active = {}
        self.data = {}
        # Autoescape turned off since HTML characters can exist in plan tracking template.
        # See details in Templates()
        self.template_env = SandboxedEnvironment(autoescape=False)

    def __getitem__(self, key):
        try:
            return self.data[key]
        except KeyError:

            connection = self.engine.raw_connection()
            cursor = connection.cursor(db.dict_cursor)

            if isinstance(key, int):
                plan_id = key
            else:
                cursor.execute('''SELECT `plan`.`id` FROM `plan` INNER JOIN `plan_active` ON `plan`.`id` = `plan_active`.`plan_id` WHERE `plan`.`name` = %s''', key)
                plan_id = cursor.fetchone()['id']

            single_plan_query = '''SELECT DISTINCT `plan`.`id` as `id`, `plan`.`name` as `name`,
                `plan`.`threshold_window` as `threshold_window`, `plan`.`threshold_count` as `threshold_count`,
                `plan`.`aggregation_window` as `aggregation_window`, `plan`.`aggregation_reset` as `aggregation_reset`,
                `plan`.`description` as `description`, UNIX_TIMESTAMP(`plan`.`created`) as `created`,
                `target`.`name` as `creator`, IF(`plan_active`.`plan_id` IS NULL, FALSE, TRUE) as `active`,
                `plan`.`tracking_type` as `tracking_type`, `plan`.`tracking_key` as `tracking_key`,
                `plan`.`tracking_template` as `tracking_template`
            FROM `plan` JOIN `target` ON `plan`.`user_id` = `target`.`id`
            LEFT OUTER JOIN `plan_active` ON `plan`.`id` = `plan_active`.`plan_id`
            WHERE `plan`.`id` = %s'''

            cursor.execute(single_plan_query, plan_id)
            plan = cursor.fetchone()

            single_plan_query_steps = '''SELECT `plan_notification`.`id` as `id`,
                `plan_notification`.`step` as `step`,
                `plan_notification`.`repeat` as `repeat`,
                `plan_notification`.`wait` as `wait`,
                `plan_notification`.`optional` as `optional`,
                `target_role`.`name` as `role`,
                `target`.`name` as `target`,
                `plan_notification`.`template` as `template`,
                `priority`.`name` as `priority`,
                `plan_notification`.`dynamic_index` AS `dynamic_index`
            FROM `plan_notification`
            LEFT OUTER JOIN `target` ON `plan_notification`.`target_id` = `target`.`id`
            LEFT OUTER JOIN `target_role` ON `plan_notification`.`role_id` = `target_role`.`id`
            JOIN `priority` ON `plan_notification`.`priority_id` = `priority`.`id`
            WHERE `plan_notification`.`plan_id` = %s
            ORDER BY `plan_notification`.`step`'''

            step = 0
            steps = []
            cursor.execute(single_plan_query_steps, plan_id)
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

            cursor.close()
            connection.close()

            logger.debug('[+] adding plan: %s', key)

            steps = {}
            for idx, notifications in enumerate(plan['steps']):
                steps[idx + 1] = [n['id'] for n in notifications]
            plan['steps'] = steps

            if plan['tracking_template']:
                tracking_template = plan['tracking_template']
                if plan['tracking_type'] == 'email':
                    for application, application_templates in tracking_template.items():
                        try:
                            tracking_template[application] = {
                                'email_subject': self.template_env.from_string(application_templates['email_subject']),
                                'email_text': self.template_env.from_string(application_templates['email_text']),
                            }
                            html_template = application_templates.get('email_html')
                            if html_template:
                                tracking_template[application]['email_html'] = self.template_env.from_string(html_template)
                        except jinja2.exceptions.TemplateSyntaxError:
                            logger.exception('[-] error parsing Plan template for %s: %s', key, application)
                            continue
                else:
                    for application, application_templates in tracking_template.items():
                        try:
                            tracking_template[application] = {
                                'body': self.template_env.from_string(application_templates['body']),
                            }
                        except jinja2.exceptions.TemplateSyntaxError:
                            logger.exception('[-] error parsing Plan template for %s: %s', key, application)
                            continue
                plan['tracking_template'] = tracking_template

            self.data[key] = plan
            return plan

    def refresh(self):
        logger.info('refreshing plans')

        connection = self.engine.raw_connection()
        cursor = connection.cursor(db.dict_cursor)

        cursor.execute('''SELECT `plan`.`id`, `plan`.`name` FROM `plan` INNER JOIN `plan_active` ON `plan`.`id` = `plan_active`.`plan_id`''')
        active = {row['id']: row['name'] for row in cursor}

        cursor.close()
        connection.close()

        new_active_ids = active.keys()
        old_active_ids = self.active.keys()

        old_ids = old_active_ids - new_active_ids
        new_ids = new_active_ids - old_active_ids

        for plan_id in old_ids:
            if self.data.get(plan_id):
                try:
                    del self.data[plan_id]
                except KeyError:
                    logger.debug('Failed pruning old plan_id %s', plan_id)

        Pool(30).map(self.__getitem__, (active[id] for id in new_ids))

        self.active = active


class TargetReprioritization(object):
    def __init__(self, engine):
        self.engine = engine
        # (target, src_mode): (dst_mode, destination, count, deque)
        self.rates = {}

    def refresh(self):
        while True:
            rates = {}
            connection = db.engine.raw_connection()
            cursor = connection.cursor()
            cursor.execute(
                '''SELECT
                    `target`.`name`,
                    `src_mode`.`name`,
                    `dst_mode`.`name`,
                    `target_contact`.`destination`,
                    `target_reprioritization`.`count`,
                    `target_reprioritization`.`duration`
                FROM `target_reprioritization`
                JOIN `target` ON `target_reprioritization`.`target_id` = `target`.`id`
                JOIN `mode` as `src_mode` ON `target_reprioritization`.`src_mode_id` = `src_mode`.`id`
                JOIN `mode` as `dst_mode` ON `target_reprioritization`.`dst_mode_id` = `dst_mode`.`id`
                JOIN `target_contact` ON `target_contact`.`target_id`=`target`.`id` AND `target_contact`.`mode_id` = `dst_mode`.`id`'''
            )
            for target, src_mode, dst_mode, destination, count, duration in cursor:
                if destination is None:
                    logger.info('invalid target reprioritization rule (%s, %s): (%s, %s, %d, %d)',
                                target, src_mode, dst_mode, destination, count, duration)
                    continue
                rates[(target, src_mode)] = (dst_mode, destination, count, duration / 60)

            cursor.close()
            connection.close()

            current = rates.keys()
            old = self.rates.keys()

            # purge old rate entries
            for key in old - current:
                logger.debug('deleting target reprioritization rule for %r: %r', key, self.rates[key])
                del self.rates[key]

            # new rate entries:
            for key in current - old:
                logger.debug('creating target reprioritization rule for %r: %r', key, rates[key])
                dst_mode, destination, count, duration_min = rates[key]
                self.rates[key] = (dst_mode, destination, count, deque([0] * duration_min, maxlen=duration_min))

            # loop through existing entries
            # if the settings have changed, gracefully alter them
            # either way, push in a new bucket
            for key in current & old:
                current_dst_mode, current_destination, current_count, current_duration_min = rates[key]
                old_dst_mode, old_destination, old_count, old_buckets = self.rates[key]
                if old_dst_mode != current_dst_mode or old_destination != current_destination or old_count != current_count or len(old_buckets) != current_duration_min:  # noqa FIXME: refactor this line
                    logger.debug('updating target reprioritization rule for %r: %r | %r', key, self.rates[key], rates[key])
                    # create a new bucket truncating if it's smaller and growing if it is larger, while preserving the counts
                    current_buckets = deque(old_buckets, maxlen=current_duration_min)
                    self.rates[key] = (current_dst_mode, current_destination, current_count, current_buckets)
                # add the new interval bucket to each
                self.rates[key][-1].append(0)

            logger.info('refreshed target reprioritization rules: %d', len(self.rates))
            logger.debug(self.rates)
            sleep(60)

    def __call__(self, message, seen=None):
        original_mode = message.get('mode')

        if not original_mode:
            return

        if seen is None:
            seen = set([original_mode])
        else:
            if original_mode in seen:
                logger.info('target reprioritization loop detected for %s, %s: %r',
                            message['target'], original_mode, seen)
                return
            else:
                seen.add(original_mode)
        try:
            dst_mode, destination, count, buckets = self.rates[(message['target'], original_mode)]
            logger.debug('reprioritization (%s, %s): (%s, %s, %d, %r)',
                         message['target'], original_mode, dst_mode, destination, count, buckets)
            # increment the bucket for this minute
            buckets[-1] += 1
            if sum(buckets) > count:
                logger.debug('target reprioritization rule triggered (%s, %s): (%s, %s, %d, %r)',
                             message['target'], original_mode, dst_mode, destination, count, buckets)
                # sum of all counts for duration exceeds count
                # reprioritize to destination mode
                message['mode'] = dst_mode
                message['destination'] = destination
                update_message_mode(message)
                self.__call__(message, seen)
                auditlog.message_change(message['message_id'], auditlog.MODE_CHANGE, original_mode, dst_mode, 'Changing mode due to reprioritization')
            else:
                return
        except KeyError:
            # target has no reprioritization rules defined
            # leave existing mode
            return


class RoleTargets():
    def __init__(self, role_lookups, engine):
        self.data = {}
        self.role_lookups = role_lookups
        self.engine = engine
        self.active_targets = set()
        self.initialize_active_targets()

    def __call__(self, role, target):
        try:
            return self.data[(role, target)]
        except KeyError:

            names = None

            # Iterate through our role lookup modules until we find one that works.
            for role_lookup in self.role_lookups:
                names = role_lookup.get(role, target)
                if names is not None:
                    break

            if names is None:
                logger.info('All role lookups modules failed to lookup %s:%s', role, target)
                self.data[(role, target)] = None
                return None

            names = self.prune_inactive_targets(names)
            self.data[(role, target)] = names
            return names

    def purge(self):
        self.data = {}
        self.initialize_active_targets()

    def prune_inactive_targets(self, usernames):
        if not usernames:
            return []
        return self.active_targets & set(usernames)

    def initialize_active_targets(self):
        connection = self.engine.raw_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT `name` FROM `target` WHERE `active` = TRUE AND `target`.`type_id` = (SELECT `id` FROM `target_type` WHERE `name` = "user")')
        self.active_targets = {row[0] for row in cursor}
        cursor.close()
        connection.close()


def refresh():
    plans.refresh()
    templates.refresh()


def purge():
    targets.purge()
    target_names.purge()
    targets_for_role.purge()
    incidents.purge()
    dynamic_plan_map.purge()
    plan_notifications.purge()


def init(config):
    global targets_for_role, target_names, target_reprioritization, plan_notifications, targets
    global roles, incidents, templates, plans, dynamic_plan_map

    plans = Plans(db.engine)
    templates = Templates(db.engine)
    incidents = Cache(db.engine,
                      'SELECT * FROM `incident` WHERE `id`=%s',
                      'SELECT `id` from `incident` WHERE `active`=True AND `id` IN %s')
    roles = Cache(db.engine, 'SELECT * FROM `target_role` WHERE `id`=%s', None)
    targets = Cache(db.engine, 'SELECT * FROM `target` WHERE `id`=%s', None)
    plan_notifications = Cache(db.engine,
                               'SELECT * FROM `plan_notification` WHERE `id`=%s',
                               ('SELECT `plan_notification`.`id` FROM `plan_notification` '
                                'JOIN `plan_active` ON `plan_notification`.`plan_id` = `plan_active`.`plan_id` '
                                'AND `plan_notification`.`id` IN %s'))
    target_reprioritization = TargetReprioritization(db.engine)
    target_names = Cache(db.engine, 'SELECT * FROM `target` WHERE `name`=%s AND `active` = TRUE', None)
    role_lookups = get_role_lookups(config)
    targets_for_role = RoleTargets(role_lookups, db.engine)
    dynamic_plan_map = DynamicPlanMap(db.engine,
                                      'SELECT * FROM `dynamic_plan_map` WHERE `incident_id` = %s',
                                      '''SELECT dynamic_plan_map.* FROM `dynamic_plan_map`
                                         JOIN `incident` ON `incident`.`id` = `dynamic_plan_map`.`incident_id`
                                         WHERE `incident`.`active` = TRUE AND `incident_id` IN %s''')

    spawn(target_reprioritization.refresh)
