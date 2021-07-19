# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from . import db
import logging

logger = logging.getLogger(__name__)

applications = {}  # name -> dict of info
priorities = {}    # name -> dict of info
target_types = {}  # name -> id
target_roles = {}  # name -> id
modes = {}         # name -> id
slack_ids = {}     # name -> id


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


def add_slack_id(username, slack_id):
    global slack_ids
    # slack ids shouldn't change so we don't have to worry about refreshing them
    slack_ids[username] = slack_id


def init():
    cache_applications()
    cache_priorities()
    cache_target_types()
    cache_target_roles()
    cache_modes()
