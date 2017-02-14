# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from __future__ import absolute_import
from . import db

applications = {}  # name -> dict of info
priorities = {}    # name -> dict of info
target_types = {}  # name -> id
target_roles = {}  # name -> id
modes = {}         # name -> id


def cache_applications():
    connection = db.engine.raw_connection()
    cursor = connection.cursor(db.dict_cursor)
    cursor.execute('''SELECT `name`, `id`, `key`, `allow_other_app_incidents`, `allow_authenticating_users` FROM `application`''')
    apps = cursor.fetchall()
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
        applications[app['name']] = app
    connection.close()
    cursor.close()


def cache_priorities():
    connection = db.engine.raw_connection()
    cursor = connection.cursor(db.dict_cursor)
    cursor.execute('''SELECT `priority`.`id`, `priority`.`name`, `priority`.`mode_id`
                      FROM `priority`''')
    for row in cursor:
        priorities[row['name']] = row
    cursor.close()
    connection.close()


def cache_target_types():
    connection = db.engine.raw_connection()
    cursor = connection.cursor()
    cursor.execute('''SELECT `name`, `id` FROM target_type''')
    target_types.update(cursor)
    cursor.close()
    connection.close()


def cache_target_roles():
    connection = db.engine.raw_connection()
    cursor = connection.cursor()
    cursor.execute('''SELECT `name`, `id` FROM target_role''')
    target_roles.update(cursor)
    cursor.close()
    connection.close()


def cache_modes():
    connection = db.engine.raw_connection()
    cursor = connection.cursor()
    cursor.execute('''SELECT `name`, `id` FROM mode''')
    modes.update(cursor)
    cursor.close()
    connection.close()


def init():
    cache_applications()
    cache_priorities()
    cache_target_types()
    cache_target_roles()
    cache_modes()
