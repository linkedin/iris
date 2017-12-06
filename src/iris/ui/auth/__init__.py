# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from iris import db


def login_user(req, username):
    session = req.env['beaker.session']
    session['user'] = username
    session.save()


def logout_user(req):
    session = req.env['beaker.session']
    session.pop('user', None)
    session.delete()


def valid_username(username):
    connection = db.engine.raw_connection()
    cursor = connection.cursor()
    cursor.execute('''
    SELECT EXISTS(SELECT 1
                  FROM `target`
                  JOIN `user` on `target`.`id` = `user`.`target_id`
                  WHERE `name` = %s AND `type_id` = (SELECT `id` FROM `target_type` WHERE `name` = "user"))''', username)
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return result[0] == 1
