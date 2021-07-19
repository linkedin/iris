# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

# -*- coding:utf-8 -*-


from phonenumbers import (format_number as pn_format_number, parse as pn_parse,
                          PhoneNumberFormat)
from gevent import sleep
import datetime
import ujson
from . import db
import re
import msgpack
import logging

logger = logging.getLogger(__name__)

uuid4hex = re.compile('[0-9a-f]{32}\Z', re.I)
allowed_text_response_actions = frozenset(['suppress', 'claim'])


def normalize_phone_number(num):
    return pn_format_number(pn_parse(num, 'US'),
                            PhoneNumberFormat.INTERNATIONAL)


def validate_msg_id(msg_id):
    return msg_id.isdigit() or uuid4hex.match(msg_id)


def parse_response(response, mode, source):
    claim_all = False
    claim_last = False
    if response.lower().startswith('f'):
        return None, 'Sincerest apologies'
    # One-letter shortcuts for claim all/last
    elif re.match('^a\s*$', response, re.IGNORECASE):
        claim_all = True
    elif re.match('^l\s*$', response, re.IGNORECASE):
        claim_last = True

    # Skip message splitting for single-letter responses
    if not (claim_all or claim_last):
        halves = response.split(None, 1)

        # $id cmd (args..)
        cmd = halves[1].split()[0].lower()
        msg_id = halves[0]
        if validate_msg_id(msg_id) and (cmd in allowed_text_response_actions):
            return msg_id, cmd

        # cmd $id (args..)
        cmd = halves[0].lower()
        msg_id = halves[1].split(None, 1)
        if len(msg_id) == 1:
            args = []
        else:
            args = msg_id[1:]
        msg_id = msg_id[0]
        if validate_msg_id(msg_id) and (cmd in allowed_text_response_actions):
            return msg_id, ' '.join([cmd] + args)

    if claim_last or re.match('claim\s+last', response, re.IGNORECASE):
        target_name = lookup_username_from_contact(mode, source)
        if not target_name:
            logger.error('Failed resolving %s:%s to target name', mode, source)
            return None, 'claim'

        connection = db.engine.raw_connection()
        cursor = connection.cursor()
        cursor.execute('''SELECT `message`.`id` from `message`
                          JOIN `target` on `target`.`id` = `message`.`target_id`
                          JOIN `target_type` on `target`.`type_id` = `target_type`.`id`
                          WHERE `target`.`name` = %s
                          AND `target_type`.`name` = 'user'
                          ORDER BY `message`.`id` DESC
                          LIMIT 1''', (target_name, ))
        ret = cursor.fetchone()
        cursor.close()
        connection.close()

        msg_id = ret[0] if ret else None
        return msg_id, 'claim'

    elif claim_all or re.match('claim\s+all', response, re.IGNORECASE):
        target_name = lookup_username_from_contact(mode, source)
        if not target_name:
            logger.error('Failed resolving %s:%s to target name', mode, source)
            return None, 'claim_all'

        connection = db.engine.raw_connection()
        cursor = connection.cursor()
        cursor.execute('''SELECT `message`.`id` from `message`
                          JOIN `target` on `target`.`id` = `message`.`target_id`
                          JOIN `incident` on `incident`.`id` = `message`.`incident_id`
                          JOIN `target_type` on `target`.`type_id` = `target_type`.`id`
                          WHERE `target`.`name` = %s
                          AND `target_type`.`name` = 'user'
                          AND `incident`.`active` = TRUE''', (target_name, ))
        msg_ids = [row[0] for row in cursor]
        cursor.close()
        connection.close()

        return msg_ids, 'claim_all'

    return halves


def parse_email_response(first_line, subject, source):
    if subject and first_line in allowed_text_response_actions:
        subject_parts = subject.strip().split(None, 2)
        if len(subject_parts) > 1 and subject_parts[0] == 'Re:' and validate_msg_id(subject_parts[1]):
            return subject_parts[1], first_line
    return parse_response(first_line, 'email', source)


def get_incident_id_from_message_id(msg_id):
    sql = 'SELECT `message`.`incident_id` FROM `message` WHERE `message`.`id` = %s'
    connection = db.engine.raw_connection()
    cursor = connection.cursor()
    cursor.execute(sql, (msg_id, ))
    ret = cursor.fetchone()
    cursor.close()
    connection.close()
    return ret[0] if ret else None


def get_incident_ids_from_message_ids(msg_ids):
    sql = 'SELECT DISTINCT `message`.`incident_id` FROM `message` WHERE `message`.`id` in %s'
    connection = db.engine.raw_connection()
    cursor = connection.cursor()
    cursor.execute(sql, (tuple(msg_ids), ))
    ret = [row[0] for row in cursor]
    cursor.close()
    connection.close()
    return ret


def get_incident_context_from_message_id(msg_id):
    sql = '''SELECT `incident`.`context`
             FROM `message`
             JOIN `incident` ON `incident`.`id` = `message`.`incident_id`
             WHERE `message`.`id` = %s'''
    connection = db.engine.raw_connection()
    cursor = connection.cursor()
    cursor.execute(sql, (msg_id, ))
    ret = cursor.fetchone()
    cursor.close()
    connection.close()
    if not ret:
        return None
    return ujson.loads(ret[0])


def get_incident_context_from_batch_id(batch_id):
    """
    Return a list of contexts for a batch of messages identified by the batch id
    """
    connection = db.engine.raw_connection()
    cursor = connection.cursor()
    sql = '''SELECT `incident`.`context`
             FROM `message`
             JOIN `incident` ON `incident`.`id` = `message`.`incident_id`
             WHERE `message`.`batch` = %s'''
    cursor.execute(sql, (batch_id, ))
    contexts = [ujson.loads(row[0]) for row in cursor]
    cursor.close()
    connection.close()
    return contexts


def lookup_username_from_contact(mode, destination):
    if mode == 'sms' or mode == 'call':
        dest = normalize_phone_number(destination)
    else:
        dest = destination
    sql = '''SELECT `target`.`name` FROM `target`
             JOIN `target_contact` on `target_contact`.`target_id` = `target`.`id`
             JOIN `mode` on `mode`.`id` = `target_contact`.`mode_id`
             WHERE `mode`.`name` = %(mode)s AND `target_contact`.`destination` = %(dest)s'''

    connection = db.engine.raw_connection()
    cursor = connection.cursor()
    cursor.execute(sql, {'mode': mode, 'dest': dest})
    ret = cursor.fetchone()
    cursor.close()
    connection.close()

    return ret[0] if ret else None


def claim_incident(incident_id, owner):
    connection = db.engine.raw_connection()

    cursor = connection.cursor()
    cursor.execute('''
      SELECT `target`.`name`
      FROM `incident`
      LEFT JOIN `target` ON `target`.`id` = `incident`.`owner_id`
      WHERE `incident`.`id` = %s
    ''', (incident_id, ))
    result = cursor.fetchone()
    previous_owner = result[0] if result else None
    cursor.close()

    active = 0 if owner else 1
    now = datetime.datetime.utcnow()

    max_retries = 3

    for i in range(max_retries):
        cursor = connection.cursor()
        try:
            cursor.execute('''UPDATE `incident`
                               SET `incident`.`updated` = %(updated)s,
                                   `incident`.`active` = %(active)s,
                                   `incident`.`owner_id` = (SELECT `target`.`id` FROM `target` WHERE `target`.`name` = %(owner)s AND `type_id` = (SELECT `id` FROM `target_type` WHERE `name` = 'user'))
                               WHERE `incident`.`id` = %(incident_id)s''',
                           {'incident_id': incident_id, 'active': active, 'owner': owner, 'updated': now})

            connection.commit()
            break
        except Exception:
            logger.exception('Failed running claim query. (Try %s/%s)', i + 1, max_retries)
        finally:
            cursor.close()

        sleep(.2)

    cursor = connection.cursor()

    try:
        cursor.execute('UPDATE `message` SET `active` = 0 WHERE `incident_id`= %s', (incident_id, ))
        connection.commit()
    except Exception:
        logger.exception('Failed running query to set message for incident %s inactive', incident_id)
    finally:
        cursor.close()

    connection.close()

    return active == 1, previous_owner


def claim_bulk_incidents(incident_ids, owner):
    incident_ids = tuple(incident_ids)
    active = 0 if owner else 1
    now = datetime.datetime.utcnow()

    connection = db.engine.raw_connection()
    cursor = connection.cursor()

    cursor.execute('''UPDATE `incident`
                      SET `incident`.`updated` = %(updated)s,
                          `incident`.`active` = %(active)s,
                          `incident`.`owner_id` = (SELECT `target`.`id` FROM `target` WHERE `target`.`name` = %(owner)s AND `type_id` = (SELECT `id` FROM `target_type` WHERE `name` = 'user'))
                       WHERE `incident`.`id` IN %(incident_ids)s''',
                   {'incident_ids': incident_ids, 'active': active, 'owner': owner, 'updated': now})

    connection.commit()

    cursor.execute('UPDATE `message` SET `active` = 0 WHERE `incident_id` IN %s', (incident_ids, ))

    connection.commit()

    claimed = set()
    not_claimed = set()

    cursor.execute('SELECT `id`, `active` FROM `incident` WHERE `id` IN %s', (incident_ids, ))

    for incident_id, active in cursor:
        if active == 1:
            not_claimed.add(incident_id)
        else:
            claimed.add(incident_id)

    cursor.close()
    connection.close()

    return claimed, not_claimed


def claim_incidents_from_batch_id(batch_id, owner):
    sql = '''UPDATE `incident`
             JOIN `message` ON `message`.`incident_id` = `incident`.`id`
             SET `incident`.`owner_id` = (SELECT `target`.`id` FROM `target` WHERE `target`.`name` = %(owner)s AND `target`.`type_id` = (SELECT `id` FROM `target_type` WHERE `name` = 'user')),
                 `incident`.`updated` = %(now)s, `incident`.`active` = 0
             WHERE `message`.`batch` = %(batch_id)s'''

    args = {
        'batch_id': batch_id,
        'owner': owner,
        'now': datetime.datetime.utcnow(),
    }

    connection = db.engine.raw_connection()
    cursor = connection.cursor()

    cursor.execute(sql, args)

    connection.commit()

    cursor.execute('''UPDATE `message` `a`
                      JOIN `message` `b` ON `a`.`incident_id` = `b`.`incident_id`
                      SET `a`.`active` = 0 WHERE `b`.`batch` = %s''',
                   (batch_id, ))

    connection.commit()

    cursor.close()
    connection.close()


def resolve_incident(incident_id, resolved_state):

    now = datetime.datetime.utcnow()
    resolved = 1
    if not resolved_state:
        resolved = 0

    connection = db.engine.raw_connection()
    cursor = connection.cursor()
    try:
        cursor.execute('''UPDATE `incident`
                        SET `incident`.`updated` = %(updated)s,
                            `incident`.`resolved` = %(resolved)s
                            WHERE `incident`.`id` = %(incident_id)s''',
                       {'incident_id': incident_id, 'resolved': resolved, 'updated': now})

        connection.commit()
    except Exception:
        logger.exception('failed updating resolved state for incident %s', incident_id)
        raise
    finally:
        cursor.close()
        connection.close()


def msgpack_unpack_msg_from_socket(socket):
    unpacker = msgpack.Unpacker()
    while True:
        buf = socket.recv(1024)
        if not buf:
            break
        unpacker.feed(buf)
        try:
            item = next(unpacker)
        except StopIteration:
            pass
        else:
            return item


def sanitize_unicode_dict(d):
    '''Properly decode unicode strings in d to avoid breaking jinja2 renderer'''
    for key, value in d.items():
        if isinstance(value, bytes):
            try:
                d[key] = value.decode('utf-8')
            except UnicodeError:
                pass
        elif isinstance(value, dict):
            d[key] = sanitize_unicode_dict(value)
    return d
