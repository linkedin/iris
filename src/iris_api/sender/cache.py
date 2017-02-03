# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from __future__ import absolute_import

from collections import deque
import requests
import jinja2
from jinja2.sandbox import SandboxedEnvironment
from gevent import spawn, sleep
from gevent.pool import Pool
from .message import update_message_mode
from .. import db
from ..role_lookup import get_role_lookup
from ..metrics import stats
from . import auditlog
from time import time
import hmac
import hashlib
import base64

import logging
logger = logging.getLogger(__name__)

# FIXME: remove this when we move to py27
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
logging.getLogger('requests').setLevel(logging.WARNING)


iris_client = None
plans = None
templates = None
incidents = None
roles = None
targets = None
plan_notifications = None
target_reprioritization = None
target_names = None
targets_for_role = None
application_quotas = None


class IrisAuth(requests.auth.AuthBase):
    def __init__(self, app, key):
        self.header = 'hmac %s:' % app
        self.HMAC = hmac.new(key, '', hashlib.sha512)

    def __call__(self, request):
        HMAC = self.HMAC.copy()
        path = request.path_url
        method = request.method
        body = request.body or ''
        window = int(time()) // 5
        HMAC.update('%s %s %s %s' % (window, method, path, body))
        digest = base64.urlsafe_b64encode(HMAC.digest())
        request.headers['Authorization'] = self.header + digest
        return request


class IrisClient(requests.Session):
    def __init__(self, base, version=0, api_auth=None):
        super(IrisClient, self).__init__()
        self.url = base + '/v%d/' % version
        adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100)
        self.mount('http://', adapter)
        self.mount('https://', adapter)
        if api_auth:
            self.iris_auth = IrisAuth(api_auth['app'], api_auth['key'])
        else:
            logger.warning('No API keys configured for sender API auth; we likely won\'t be able to send quota notifications')
            self.iris_auth = None

    def get(self, path, *args, **kwargs):
        return super(IrisClient, self).get(self.url + path, *args, **kwargs)

    def post(self, path, *args, **kwargs):
        if self.iris_auth:
            kwargs['auth'] = self.iris_auth
        return super(IrisClient, self).post(self.url + path, *args, **kwargs)


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
            for key in self.data.viewkeys() - {row[0] for row in cursor}:
                del self.data[key]
            cursor.close()
            connection.close()


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
            cursor.execute('''SELECT `template`.`id`, `application`.`name`, `mode`.`name`, `template_content`.`subject`, `template_content`.`body`
                FROM `template_active`
                JOIN `template` ON `template`.`id` = `template_active`.`template_id`
                JOIN `template_content` ON `template_content`.`template_id` = `template_active`.`template_id`
                JOIN `application` ON `template_content`.`application_id` = `application`.`id`
                JOIN `mode` ON `template_content`.`mode_id` = `mode`.`id`
                WHERE `template_active`.`name` = %s''', key)

            for template_id, application, mode, subject, body in cursor:
                logger.debug('[+] adding template: %s %s %s %s', key, template_id, application, mode)
                try:
                    if self.has_message_id(subject) or self.has_message_id(body):
                        subject = self.env.from_string(subject)
                        body = self.env.from_string(body)
                    else:
                        subject = self.env.from_string('{{ iris.message_id }} ' + subject)
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

        templates_response = iris_client.get('templates/?active=1&fields=id&fields=name').json()

        active = {item['id']: item['name'] for item in templates_response}

        new_active_ids = active.viewkeys()
        old_active_ids = self.active.viewkeys()

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
        self.template_env = SandboxedEnvironment(autoescape=True)

    def __getitem__(self, key):
        try:
            return self.data[key]
        except KeyError:
            fields = ['threshold_window', 'threshold_count', 'aggregation_window', 'creator',
                      'aggregation_reset', 'name', 'tracking_type', 'tracking_key', 'tracking_template']
            plan = iris_client.get('plans/%s/' % key, params={'fields': fields}).json()
            logger.debug('[+] adding plan: %s', key)

            steps = {}
            for idx, notifications in enumerate(plan['steps']):
                steps[idx + 1] = [n['id'] for n in notifications]
            plan['steps'] = steps

            if plan['tracking_template']:
                tracking_template = plan['tracking_template']
                if plan['tracking_type'] == 'email':
                    for application, application_templates in tracking_template.iteritems():
                        tracking_template[application] = {
                            'email_subject': self.template_env.from_string(application_templates['email_subject']),
                            'email_text': self.template_env.from_string(application_templates['email_text']),
                        }
                        html_template = application_templates.get('email_html')
                        if html_template:
                            tracking_template[application]['email_html'] = self.template_env.from_string(html_template)
                    plan['tracking_template'] = tracking_template
                else:
                    # not supported type, set to None
                    plan['tracking_template'] = None

            self.data[key] = plan
            return plan

    def refresh(self):
        logger.info('refreshing plans')

        plans_response = iris_client.get('plans/?active=1&fields=id&fields=name').json()

        active = {item['id']: item['name'] for item in plans_response}

        new_active_ids = active.viewkeys()
        old_active_ids = self.active.viewkeys()

        old_ids = old_active_ids - new_active_ids
        new_ids = new_active_ids - old_active_ids

        for plan_id in old_ids:
            try:
                del self.data[plan_id]
            except KeyError:
                logger.exception('Failed pruning old plan_id %s', plan_id)

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

            current = rates.viewkeys()
            old = self.rates.viewkeys()

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
        if seen is None:
            seen = set([message['mode']])
        else:
            if message['mode'] in seen:
                logger.info('target reprioritization loop detected for %s, %s: %r',
                            message['target'], message['mode'], seen)
                return
            else:
                seen.add(message['mode'])
        try:
            dst_mode, destination, count, buckets = self.rates[(message['target'], message['mode'])]
            logger.debug('reprioritization (%s, %s): (%s, %s, %d, %r)',
                         message['target'], message['mode'], dst_mode, destination, count, buckets)
            # increment the bucket for this minute
            buckets[-1] += 1
            if sum(buckets) > count:
                logger.debug('target reprioritization rule triggered (%s, %s): (%s, %s, %d, %r)',
                             message['target'], message['mode'], dst_mode, destination, count, buckets)
                # sum of all counts for duration exceeds count
                # reprioritize to destination mode
                old_mode = message['mode']
                message['mode'] = dst_mode
                message['destination'] = destination
                update_message_mode(message)
                self.__call__(message, seen)
                auditlog.message_change(message['message_id'], auditlog.MODE_CHANGE, old_mode, dst_mode, 'Changing mode due to reprioritization')
            else:
                return
        except KeyError:
            # target has no reprioritization rules defined
            # leave existing mode
            return


class ApplicationQuotas(object):

    def __init__(self, engine, iris_client):
        self.engine = engine
        self.iris_client = iris_client
        self.rates = {}  # application: (hard_buckets, soft_buckets, hard_limit, soft_limit, wait_time, plan_name, (target_name, target_role))
        self.last_incidents = {}  # application: (incident_id, time())

    def refresh(self):
        while True:
            logging.info('Refreshing app quotas')
            new_rates = {}
            connection = self.engine.raw_connection()
            cursor = connection.cursor()
            cursor.execute('''SELECT `application`.`name` as application,
                                     `application_quotas`.`hard_quota_threshold`,
                                     `application_quotas`.`soft_quota_threshold`,
                                     `application_quotas`.`hard_quota_duration`,
                                     `application_quotas`.`soft_quota_duration`,
                                     `target`.`name` as target_name,
                                     `target_type`.`name` as target_role,
                                     `application_quotas`.`plan_name`,
                                     `application_quotas`.`wait_time`
                              FROM `application_quotas`
                              JOIN `application` ON `application`.`id` = `application_quotas`.`application_id`
                              JOIN `target` on `target`.`id` = `application_quotas`.`target_id`
                              JOIN `target_type` on `target_type`.`id` = `target`.`type_id`''')

            for application, hard_limit, soft_limit, hard_duration, soft_duration, target_name, target_role, plan_name, wait_time in cursor:
                new_rates[application] = (hard_limit, soft_limit, hard_duration / 60, soft_duration / 60, wait_time, plan_name, (target_name, target_role))

            cursor.close()
            connection.close()

            old_keys = self.rates.viewkeys()
            new_keys = new_rates.viewkeys()

            # Remove old application entries
            for key in old_keys - new_keys:
                logger.info('Pruning old application quota for %s', key)
                try:
                    del(self.rates[key])
                    del(self.last_incidents[key])
                except KeyError:
                    pass

            # Create new ones with fresh buckets
            for key in new_keys - old_keys:
                hard_limit, soft_limit, hard_duration, soft_duration, wait_time, plan_name, target = new_rates[key]
                self.rates[key] = (deque([0] * hard_duration, maxlen=hard_duration),  # hard buckets
                                   deque([0] * soft_duration, maxlen=soft_duration),  # soft buckets
                                   hard_limit, soft_limit, wait_time, plan_name, target)

            # Update existing ones + append new time interval. Keep same time bucket object if duration hasn't changed, otherwise create new
            # one and resize accordingly
            for key in new_keys & old_keys:
                hard_limit, soft_limit, hard_duration, soft_duration, wait_time, plan_name, target = new_rates[key]
                self.rates[key] = (self.rates[key][0] if len(self.rates[key][0]) == hard_duration else deque(self.rates[key][0], maxlen=hard_duration),
                                   self.rates[key][1] if len(self.rates[key][1]) == soft_duration else deque(self.rates[key][1], maxlen=soft_duration),
                                   hard_limit, soft_limit, wait_time, plan_name, target)

                # Increase minute interval for hard + soft buckets
                self.rates[key][0].append(0)
                self.rates[key][1].append(0)

            logging.info('Refreshed app quotas: %s', self.rates.keys())
            sleep(60)

    def __call__(self, message):
        application = message.get('application')

        if not application:
            return True

        rate = self.rates.get(application)

        if not rate:
            return True

        hard_buckets, soft_buckets, hard_limit, soft_limit, wait_time, plan_name, target = rate

        # Increment both buckets for this minute
        hard_buckets[-1] += 1
        soft_buckets[-1] += 1

        # If hard limit breached, disallow sending this message and create incident
        if sum(hard_buckets) > hard_limit:
            self.notify_incident(application, hard_limit, len(hard_buckets), plan_name, wait_time)
            return False

        # If soft limit breached, just notify owner and still send
        if sum(soft_buckets) > soft_limit:
            self.notify_target(application, soft_limit, len(soft_buckets), *target)
            return True

        return True

    def notify_incident(self, application, limit, duration, plan_name, wait_time):
        logger.warning('Application %s breached hard quota. Will create incident using plan %s', application, plan_name)

        # Avoid creating new incident if we have an incident that's either not claimed or claimed and wait_time hasn't been exceeded
        last_incident = self.last_incidents.get(application)
        if last_incident:
            last_incident_id, last_incident_created = last_incident
            try:
                r = self.iris_client.get('incidents/%s' % last_incident_id)
                r.raise_for_status()
                last_incident = r.json()
            except (requests.exceptions.RequestException, ValueError):
                logger.exception('Failed looking up last created incident %s for application %s during hard quota breach', last_incident_id, application)
            else:
                try:
                    if last_incident['active']:
                        logger.info('Skipping creating incident for application %s as existing incident %s is not claimed', application, last_incident_id)
                        return

                    if wait_time and (time() - last_incident_created) < wait_time:
                        logger.info('Skipping creating incident for application %s as it is not yet %s seconds since existing incident %s was claimed',
                                    application, wait_time, last_incident_id)
                        return
                except KeyError:
                    logger.exception('Failed parsing info for incident %s during application %s hard quota breach', last_incident_id, application)

        # Make a new incident
        try:
            r = self.iris_client.post('incidents', json={
                'plan': plan_name,
                'context': {
                  'feature': 'quota-breach',
                  'details': {
                    'application': application,
                    'limit': limit,
                    'duration': duration
                  }
                }
            })
            r.raise_for_status()
            incident_id = r.json()
            self.last_incidents[application] = incident_id, time()
            logger.info('Created incident %s', incident_id)
        except (requests.exceptions.RequestException, ValueError):
            logger.exception('Failed hitting iris-api to create incident for application %s breaching hard quota', application)

    def notify_target(self, application, limit, duration, target_name, target_role):
        logger.warning('Application %s breached soft quota. Will notify %s:%s', application, target_role, target_name)

        try:
            self.iris_client.post('notifications', json={
              'priority': 'low',
              'target': target_name,
              'role': target_role,
              'subject': 'Application %s exceeding message quota' % application,
              'body': ('Hi\n\nYour application %s is currently exceeding its soft quota of %s messages per %s minutes.\n\n'
                       'If this continues, your messages will eventually be dropped on the floor and an Iris incident will be raised.\n\n'
                       'Regards,\nIris') % (application, limit, duration, )
            }).raise_for_status()
        except requests.exceptions.RequestException:
            logger.exception('Failed hitting iris-api to create incident for application %s breaching hard quota', application)


class RoleTargets():
    def __init__(self, role_lookup, engine):
        self.data = {}
        self.role_lookup = role_lookup
        self.engine = engine
        self.active_targets = set()
        self.initialize_active_targets()

    def __call__(self, role, target):
        try:
            return self.data[(role, target)]
        except KeyError:
            names = []
            if role == 'user':
                names = [target]
            elif role == 'team':
                names = self.role_lookup.team_members(target)
                if names is None:
                    stats['oncall_error'] += 1
                    return None
            elif role == 'manager':
                names = self.role_lookup.team_manager(target)
                if names is None:
                    stats['oncall_error'] += 1
                    return None
            elif role.startswith('oncall'):
                names = self.role_lookup.team_oncall(target, 'primary' if role == 'oncall' else role[7:])
                if names is None:
                    stats['oncall_error'] += 1
                    return None
            else:
                names = []

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
        cursor.execute('SELECT `name` FROM `target` WHERE `active` = TRUE')
        self.active_targets = {row[0] for row in cursor}
        cursor.close()
        connection.close()


def refresh():
    plans.refresh()
    templates.refresh()


def purge():
    target_names.purge()
    targets_for_role.purge()
    incidents.purge()


def init(config):
    global targets_for_role, target_names, target_reprioritization, plan_notifications, targets
    global roles, incidents, templates, plans, iris_client, application_quotas

    iris_client = IrisClient(config['sender'].get('api_host', 'http://localhost:16649'), 0, config['sender'].get('api_auth'))
    plans = Plans(db.engine)
    templates = Templates(db.engine)
    incidents = Cache(db.engine,
                      'SELECT * FROM `incident` WHERE `id`=%s',
                      'SELECT `id` from `incident` WHERE `active`=True AND `id` IN %s')
    roles = Cache(db.engine, 'SELECT * FROM `target_role` WHERE `id`=%s', None)
    # TODO: purge based on target acive column?
    targets = Cache(db.engine, 'SELECT * FROM `target` WHERE `id`=%s', None)
    # TODO: also purge this cache?
    plan_notifications = Cache(db.engine,
                               'SELECT * FROM `plan_notification` WHERE `id`=%s',
                               ('SELECT `plan_notification`.`id` FROM `plan_notification` '
                                'JOIN `plan_active` ON `plan_notification`.`plan_id` = `plan_active`.`plan_id` '
                                'AND `plan_notification`.`id` IN %s'))
    target_reprioritization = TargetReprioritization(db.engine)
    application_quotas = ApplicationQuotas(db.engine, iris_client)
    target_names = Cache(db.engine, 'SELECT * FROM `target` WHERE `name`=%s', None)
    role_lookup = get_role_lookup(config)
    targets_for_role = RoleTargets(role_lookup, db.engine)

    spawn(target_reprioritization.refresh)
    spawn(application_quotas.refresh)
