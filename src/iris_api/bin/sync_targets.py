# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from gevent import monkey, sleep, spawn
monkey.patch_all()  # NOQA

import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import requests
import ldap
from phonenumbers import format_number, parse, PhoneNumberFormat
from phonenumbers.phonenumberutil import NumberParseException

from ldap.controls import SimplePagedResultsControl
from iris_api.api import load_config_file
from iris_api.metrics import stats, init as init_metrics, emit_metrics

from requests.packages.urllib3.exceptions import (
    InsecureRequestWarning, SNIMissingWarning, InsecurePlatformWarning
)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(SNIMissingWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
logging.getLogger('requests').setLevel(logging.WARNING)


stats_reset = {
    'ldap_found': 0,
    'sql_errors': 0,
    'users_added': 0,
    'users_failed_to_add': 0,
    'users_failed_to_update': 0,
    'users_purged': 0,
    'teams_added': 0,
    'teams_failed_to_add': 0,
    'user_contacts_updated': 0,
}

logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(ch)


def normalize_phone_number(num):
    return format_number(parse(num.decode('utf-8'), 'US'),
                         PhoneNumberFormat.INTERNATIONAL)


def get_predefined_users(config):
    users = {}
    config_users = []

    try:
        config_users = config['sync_script']['preset_users']
    except KeyError:
        return {}

    for user in config_users:
        users[user['name']] = user
        for key in ['sms', 'call']:
            try:
                users[user['name']][key] = normalize_phone_number(users[user['name']][key])
            except (NumberParseException, KeyError, AttributeError):
                users[user['name']][key] = None

    return users


def prune_user(engine, username):
    stats['users_purged'] += 1

    try:
        engine.execute('DELETE FROM `target` WHERE `name` = %s', username)
        logger.info('Deleted inactive user %s', username)

    # The user has messages or some other user data which should be preserved.
    # Just mark as inactive.
    except IntegrityError:
        logger.info('Marking user %s inactive', username)
        engine.execute('UPDATE `target` SET `active` = FALSE WHERE `name` = %s', username)

    except SQLAlchemyError as e:
        logger.error('Deleting user %s failed: %s', username, e)
        stats['sql_errors'] += 1


def fetch_ldap(config):

    ldap_config = config['ldap']

    # Some ldap settings are global and need to be set before we initialize
    global_ldap_keys = set([ldap.OPT_X_TLS_REQUIRE_CERT])
    for key in global_ldap_keys:
        if key in ldap_config['options']:
            ldap.set_option(key, ldap_config['options'][key])

    l = ldap.initialize(ldap_config['url'])

    for key in ldap_config['options'].viewkeys() - global_ldap_keys:
        l.set_option(key, ldap_config['options'][key])

    l.simple_bind_s(ldap_config['user'], ldap_config['pass'])

    req_ctrl = SimplePagedResultsControl(True, size=1000, cookie='')

    known_ldap_resp_ctrls = {
        SimplePagedResultsControl.controlType: SimplePagedResultsControl,
    }

    dn_map = {}
    users = {}

    while True:
        msgid = l.search_ext(ldap_config['search_base'],
                             ldap.SCOPE_SUBTREE,
                             ldap_config['search_query'],
                             ldap_config['search_attrs'],
                             serverctrls=[req_ctrl])
        rtype, rdata, rmsgid, serverctrls = l.result3(msgid, resp_ctrl_classes=known_ldap_resp_ctrls)
        logger.info('Loaded %d entries from ldap.' % len(rdata))
        for dn, ldap_dict in rdata:
            if 'mail' not in ldap_dict:
                logger.error('ERROR: invalid ldap entry for dn: %s' % dn)
                continue

            name = ldap_dict['sAMAccountName'][0]

            mobile = ldap_dict.get('mobile')
            mail = ldap_dict.get('mail')
            manager = ldap_dict.get('manager')

            if mobile:
                try:
                    mobile = normalize_phone_number(mobile[0])
                except NumberParseException:
                    mobile = None

            if mail:
                mail = mail[0]
                slack = mail.split('@')[0]

            if manager:
                manager = manager[0]

            contacts = {'call': mobile, 'sms': mobile, 'email': mail,
                        'slack': slack, 'manager': manager}
            dn_map[dn] = name
            users[name] = contacts

        pctrls = [c for c in serverctrls
                  if c.controlType == SimplePagedResultsControl.controlType]

        cookie = pctrls[0].cookie
        if not cookie:
            break
        req_ctrl.cookie = cookie

    for user in users:
        if not users[user]['manager']:
            logger.debug('%s does not have a manager' % user)
            continue
        try:
            users[user]['manager'] = dn_map[users[user]['manager']]
        except KeyError:
            logger.warning('Cannot resolve full name for %s\'s manager' % user)

    return users


def sync(config, engine, purge_old_users=True):
    session = sessionmaker(bind=engine)()
    # iris
    iris_users = {}
    for row in engine.execute('''SELECT `target`.`name` as `name`, `mode`.`name` as `mode`,
                                        `target_contact`.`destination`
                                 FROM `target`
                                 JOIN `user` on `target`.`id` = `user`.`target_id`
                                 LEFT OUTER JOIN `target_contact` ON `target`.`id` = `target_contact`.`target_id`
                                 LEFT OUTER JOIN `mode` ON `target_contact`.`mode_id` = `mode`.`id`
                                 WHERE `target`.`active` = TRUE
                                 ORDER BY `target`.`name`'''):
        contacts = iris_users.setdefault(row.name, {})
        if row.mode is None or row.destination is None:
            continue
        contacts[row.mode] = row.destination

    iris_usernames = iris_users.viewkeys()

    # oncall
    oncall_base_url = config.get('oncall-api')
    oncall_team_names = []
    if oncall_base_url:
        try:
            re = requests.get('%s/api/v0/teams?fields=name' % oncall_base_url)
            oncall_team_names = re.json()
        except (ValueError, requests.exceptions.RequestException):
            logger.exception('Failed hitting oncall endpoint to fetch list of team names')

    if not oncall_team_names:
        logger.error('We do not have a list of team names')

    oncall_team_names = set(oncall_team_names)

    # users from ldap and config file
    ldap_users = fetch_ldap(config)
    stats['ldap_found'] += len(ldap_users)
    ldap_users.update(get_predefined_users(config))
    ldap_usernames = ldap_users.viewkeys()

    # set of ldap users not in iris
    users_to_insert = ldap_usernames - iris_usernames
    # set of existing iris users that are in ldap
    users_to_update = iris_usernames & ldap_usernames
    users_to_mark_inactive = iris_usernames - ldap_usernames

    # get objects needed for insertion
    target_types = {name: id for name, id in session.execute('SELECT `name`, `id` FROM `target_type`')}  # 'team' and 'user'
    modes = {name: id for name, id in session.execute('SELECT `name`, `id` FROM `mode`')}
    iris_team_names = {name for (name, ) in engine.execute('''SELECT `name` FROM `target` WHERE `type_id` = %s''', target_types['team'])}

    target_add_sql = 'INSERT INTO `target` (`name`, `type_id`) VALUES (%s, %s) ON DUPLICATE KEY UPDATE `active` = TRUE'
    user_add_sql = 'INSERT IGNORE INTO `user` (`target_id`) VALUES (%s)'
    target_contact_add_sql = '''INSERT INTO `target_contact` (`target_id`, `mode_id`, `destination`)
                                VALUES (%s, %s, %s)
                                ON DUPLICATE KEY UPDATE `destination` = %s'''

    # insert users that need to be
    logger.info('Users to insert (%d)' % len(users_to_insert))
    for username in users_to_insert:
        logger.info('Inserting %s' % username)
        try:
            target_id = engine.execute(target_add_sql, (username, target_types['user'])).lastrowid
            engine.execute(user_add_sql, (target_id, ))
        except SQLAlchemyError as e:
            stats['users_failed_to_add'] += 1
            stats['sql_errors'] += 1
            logger.exception('Failed to add user %s' % username)
            continue
        stats['users_added'] += 1
        for key, value in ldap_users[username].iteritems():
            if value and key in modes:
                logger.info('%s: %s -> %s' % (username, key, value))
                engine.execute(target_contact_add_sql, (target_id, modes[key], value, value))

    # update users that need to be
    contact_update_sql = 'UPDATE target_contact SET destination = %s WHERE target_id = (SELECT id FROM target WHERE name = %s) AND mode_id = %s'
    contact_insert_sql = 'INSERT INTO target_contact (target_id, mode_id, destination) VALUES ((SELECT id FROM target WHERE name = %s), %s, %s)'
    contact_delete_sql = 'DELETE FROM target_contact WHERE target_id = (SELECT id FROM target WHERE name = %s) AND mode_id = %s'

    logger.info('Users to update (%d)' % len(users_to_update))
    for username in users_to_update:
        try:
            db_contacts = iris_users[username]
            ldap_contacts = ldap_users[username]
            for mode in modes:
                if mode in ldap_contacts and ldap_contacts[mode]:
                    if mode in db_contacts:
                        if ldap_contacts[mode] != db_contacts[mode]:
                            logger.info('%s: updating %s' % (username, mode))
                            stats['user_contacts_updated'] += 1
                            engine.execute(contact_update_sql, (ldap_contacts[mode], username, modes[mode]))
                    else:
                        logger.info('%s: adding %s' % (username, mode))
                        stats['user_contacts_updated'] += 1
                        engine.execute(contact_insert_sql, (username, modes[mode], ldap_contacts[mode]))
                elif mode in db_contacts:
                    logger.info('%s: deleting %s' % (username, mode))
                    stats['user_contacts_updated'] += 1
                    engine.execute(contact_delete_sql, (username, modes[mode]))
                else:
                    logger.debug('%s: missing %s' % (username, mode))
        except SQLAlchemyError as e:
            stats['users_failed_to_update'] += 1
            stats['sql_errors'] += 1
            logger.exception('Failed to update user %s' % username)
            continue

    # sync teams between iris and oncall
    teams_to_insert = oncall_team_names - iris_team_names

    logger.info('Teams to insert (%d)' % len(teams_to_insert))
    for t in teams_to_insert:
        logger.info('Inserting %s' % t)
        try:
            target_id = engine.execute(target_add_sql, (t, target_types['team'])).lastrowid
            stats['teams_added'] += 1
        except SQLAlchemyError as e:
            logger.exception('Error inserting team %s: %s' % (t, e))
            stats['teams_failed_to_add'] += 1
            continue
    session.commit()
    session.close()

    # mark users inactive
    if purge_old_users:
        logger.info('Users to mark inactive (%d)' % len(users_to_mark_inactive))
        for username in users_to_mark_inactive:
            prune_user(engine, username)


def main():
    config = load_config_file(sys.argv[1])
    init_metrics(config, 'iris-sync-targets', stats_reset)

    default_nap_time = 3600

    try:
        nap_time = int(config.get('sync_script_nap_time', default_nap_time))
    except ValueError:
        nap_time = default_nap_time

    engine = create_engine(config['db']['conn']['str'] % config['db']['conn']['kwargs'],
                           **config['db']['kwargs'])

    spawn(emit_metrics)

    while True:
        sync(config, engine)
        logger.info('Sleeping for %d seconds' % nap_time)
        sleep(nap_time)


if __name__ == '__main__':
    main()
