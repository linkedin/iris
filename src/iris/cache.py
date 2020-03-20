# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import pylibmc
from . import db
import logging

from .config import load_config

logger = logging.getLogger(__name__)

applications = {}  # name -> dict of info
priorities = {}    # name -> dict of info
target_types = {}  # name -> id
target_roles = {}  # name -> id
modes = {}         # name -> id

quota_configs = {}


def cache_applications():
    global applications
    connection = db.engine.raw_connection()
    cursor = connection.cursor(db.dict_cursor)
    cursor.execute('''SELECT `name`, `id`, `key`, `allow_other_app_incidents`,
                             `allow_authenticating_users`, `secondary_key`
                      FROM `application`''')
    apps = cursor.fetchall()
    new_applications = {}
    for app in apps:
        cursor.execute(
            'SELECT `name` FROM `template_variable` WHERE `application_id` = %s',
            app['id'])
        app['variables'] = [row['name'] for row in cursor]
        cursor.execute('''SELECT `mode`.`name`
                          FROM `mode`
                          JOIN `application_mode` on `mode`.`id` = `application_mode`.`mode_id`
                          WHERE `application_mode`.`application_id` = %s''', app['id'])
        app['supported_modes'] = [row['name'] for row in cursor]
        cursor.execute('''SELECT `mode`.`name` AS mode_name, `application_custom_sender_address`.`sender_address` AS address
                          FROM `application_custom_sender_address`
                          JOIN `mode` on `mode`.`id` = `application_custom_sender_address`.`mode_id`
                          WHERE `application_custom_sender_address`.`application_id` = %s''', app['id'])
        app['custom_sender_addresses'] = {row['mode_name']: row['address'] for row in cursor}
        cursor.execute('''SELECT `notification_category`.`id`, `notification_category`.`name`,
                                 `notification_category`.`description`, `notification_category`.`mode_id`,
                                 `mode`.`name` AS mode
                          FROM `notification_category`
                          JOIN `mode` ON `notification_category`.`mode_id` = `mode`.`id`
                          WHERE `application_id` = %s''', app['id'])
        app['categories'] = {row['name']: row for row in cursor}
        new_applications[app['name']] = app
    applications = new_applications
    connection.close()
    cursor.close()
    logger.debug('Loaded applications: %s', ', '.join(applications))


def cache_priorities():
    global priorities
    connection = db.engine.raw_connection()
    cursor = connection.cursor(db.dict_cursor)
    cursor.execute('''SELECT `priority`.`id`, `priority`.`name`, `priority`.`mode_id`
                      FROM `priority`''')
    priorities = {row['name']: row for row in cursor}
    cursor.close()
    connection.close()


def cache_target_types():
    global target_types
    connection = db.engine.raw_connection()
    cursor = connection.cursor()
    cursor.execute('''SELECT `name`, `id` FROM target_type''')
    target_types = dict(cursor)
    cursor.close()
    connection.close()


def cache_target_roles():
    global target_roles
    connection = db.engine.raw_connection()
    cursor = connection.cursor()
    cursor.execute('''SELECT `name`, `id` FROM target_role''')
    target_roles = dict(cursor)
    cursor.close()
    connection.close()


def cache_modes():
    global modes
    connection = db.engine.raw_connection()
    cursor = connection.cursor()
    cursor.execute('''SELECT `name`, `id` FROM mode''')
    modes = dict(cursor)
    cursor.close()
    connection.close()


def check_quota_breach(plan):
    '''
        if a plan breaches the quota set by incident_quota_max
        it will no longer be able to create incidents. After
        quota_breach_duration amount of seconds from the first incident
        the plan's quota will reset.
    '''
    global quota_configs
    if quota_configs.get('disable_quota'):
        # skip quota check
        return False
    try:
        mc = pylibmc.Client([quota_configs.get('memcache_host')], binary=True, behaviors={"cas": True, "tcp_nodelay": True, "ketama": True})
        mc.get("test-key")
    except Exception as e:
        # if connecting to memcache fails disable quota and default to accepting incidents
        logger.exception('Failed conencting to memcache')
        quota_configs = {'disable_quota': True}
        return False
    # plans can have spaces and keys can't, hash to normalize keys
    plan_hash = str(hash(plan))
    if not mc.get(plan_hash):
        # set expiry to quota_breach_duration seconds, after expiry quota resets
        mc.set(plan_hash, 0, quota_configs.get('quota_breach_duration'))
    # atomic memcached-side increment operation
    mc.incr(plan_hash)
    quota_used = mc.get(plan_hash)
    if quota_used > quota_configs.get('incident_quota_max'):
        return True
    else:
        return False


def config_cache(config):
    global quota_configs
    if config.get('distributed_quota'):
        quota_configs = {
            'disable_quota': config['distributed_quota'].get('disable_quota'),
            'memcache_host': config['distributed_quota'].get('memcache_host'),
            'memcache_port': config['distributed_quota'].get('memcache_port'),
            'incident_quota_max': config['distributed_quota'].get('incident_quota_maximum'),
            'quota_breach_duration': config['distributed_quota'].get('quota_breach_duration')
        }
    else:
        quota_configs = {'disable_quota': True}


def init():
    config_cache(load_config())
    cache_applications()
    cache_priorities()
    cache_target_types()
    cache_target_roles()
    cache_modes()
