# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

# -*- coding:utf-8 -*-

from __future__ import absolute_import
from phonenumbers import (format_number as pn_format_number, parse as pn_parse,
                          PhoneNumberFormat)
import datetime
import ujson
from . import db
import re
import msgpack

uuid4hex = re.compile('[0-9a-f]{32}\Z', re.I)
allowed_text_response_actions = frozenset(['suppress', 'claim'])


def normalize_phone_number(num):
    return pn_format_number(pn_parse(num, 'US'),
                            PhoneNumberFormat.INTERNATIONAL)


def validate_msg_id(msg_id):
    return msg_id.isdigit() or uuid4hex.match(msg_id)


def parse_response(response, mode, source):
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

    if re.match('[cC]laim\s+last', response):
        session = db.Session()
        target_name = lookup_username_from_contact(mode, source, session=session)
        msg_id = session.execute('''SELECT `message`.`id` from `message`
                                    JOIN `target` on `target`.`id` = `message`.`target_id`
                                    WHERE `target`.`name` = :target_name
                                    ORDER BY `message`.`id` DESC
                                    LIMIT 1''', {'target_name': target_name}).scalar()
        session.close()
        return msg_id, 'claim'

    return halves


def parse_email_response(first_line, subject, source):
    if subject and first_line in allowed_text_response_actions:
        subject_parts = subject.strip().split(None, 2)
        if len(subject_parts) > 1 and subject_parts[0] == 'Re:' and validate_msg_id(subject_parts[1]):
            return subject_parts[1], first_line
    return parse_response(first_line, 'email', source)


def get_incident_id_from_message_id(msg_id):
    sql = 'SELECT `message`.`incident_id` FROM `message` WHERE `message`.`id` = :msg_id'
    return db.Session().execute(sql, {'msg_id': msg_id}).scalar()


def get_incident_context_from_message_id(msg_id):
    session = db.Session()
    sql = '''SELECT
               `incident`.`context`
             FROM
               `message`
               JOIN `incident` ON `incident`.`id` = `message`.`incident_id`
             WHERE
               `message`.`id` = :msg_id'''
    context = session.execute(sql, {'msg_id': msg_id}).scalar()
    if not context:
        session.close()
        return None
    context = ujson.loads(context)
    session.close()
    return context


def get_incident_context_from_batch_id(batch_id):
    """
    Return a list of contexts for a batch of messages identified by the batch id
    """
    session = db.Session()
    sql = '''SELECT
               `incident`.`context`
             FROM
               `message`
               JOIN `incident` ON `incident`.`id` = `message`.`incident_id`
             WHERE
               `message`.`batch` = :batch_id'''
    results = session.execute(sql, {'batch_id': batch_id})
    contexts = [ujson.loads(row[0]) for row in results]
    session.close()
    return contexts


def lookup_username_from_contact(mode, destination, session=None):
    if not session:
        session = db.Session()
    if mode == 'sms' or mode == 'call':
        dest = normalize_phone_number(destination)
    else:
        dest = destination
    sql = '''SELECT `target`.`name` FROM `target`
             JOIN `target_contact` on `target_contact`.`target_id` = `target`.`id`
             JOIN `mode` on `mode`.`id` = `target_contact`.`mode_id`
             WHERE `mode`.`name` = :mode AND `target_contact`.`destination` = :dest'''
    return session.execute(sql, {'mode': mode, 'dest': dest}).scalar()


def claim_incident(incident_id, owner, session=None):
    if not session:
        session = db.Session()
    active = 0 if owner else 1
    now = datetime.datetime.utcnow()
    session.execute('''UPDATE `incident`
                       SET `incident`.`updated` = :updated,
                           `incident`.`active` = :active,
                           `incident`.`owner_id` = (SELECT `target`.`id` FROM `target` WHERE `target`.`name` = :owner)
                       WHERE `incident`.`id` = :incident_id''',
                    {'incident_id': incident_id, 'active': active, 'owner': owner, 'updated': now})

    session.execute('UPDATE `message` SET `active`=0 WHERE `incident_id`=:incident_id', {'incident_id': incident_id})
    session.commit()
    session.close()

    return active == 1


def claim_incidents_from_batch_id(batch_id, owner):
    session = db.Session()
    sql = ('UPDATE incident '
           'INNER JOIN message ON (message.incident_id=incident.id) '
           'SET incident.owner_id=(SELECT target.id FROM target WHERE target.name=:owner) '
           '  , incident.updated=:now, incident.active=0 '
           'WHERE message.batch=:batch_id ')
    args = {
        'batch_id': batch_id,
        'owner': owner,
        'now': datetime.datetime.utcnow(),
    }
    session.execute(sql, args)
    session.execute('''UPDATE `message` `a`
                       JOIN `message` `b` ON `a`.`incident_id` = `b`.`incident_id`
                       SET `a`.`active`=0 WHERE `b`.`batch`=:batch''',
                    {'batch': batch_id})
    session.commit()
    session.close()


def msgpack_unpack_msg_from_socket(socket):
    unpacker = msgpack.Unpacker()
    while True:
        buf = socket.recv(1024)
        if not buf:
            break
        unpacker.feed(buf)
        try:
            item = unpacker.next()
        except StopIteration:
            pass
        else:
            return item
