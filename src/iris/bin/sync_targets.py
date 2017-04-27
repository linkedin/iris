# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from gevent import monkey, sleep, spawn
monkey.patch_all()  # NOQA

import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DataError
import requests
from phonenumbers import format_number, parse, PhoneNumberFormat
from phonenumbers.phonenumberutil import NumberParseException

from iris.api import load_config
from iris import metrics

from requests.packages.urllib3.exceptions import (
    InsecureRequestWarning, SNIMissingWarning, InsecurePlatformWarning
)

# Used for the optional ldap mailing list resolving functionality
import ldap
from ldap.controls import SimplePagedResultsControl
from ldap.filter import escape_filter_chars
import time
ldap_pagination_size = 1000

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(SNIMissingWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
logging.getLogger('requests').setLevel(logging.WARNING)


stats_reset = {
    'sql_errors': 0,
    'users_added': 0,
    'users_failed_to_add': 0,
    'users_failed_to_update': 0,
    'users_purged': 0,
    'teams_added': 0,
    'teams_failed_to_add': 0,
    'user_contacts_updated': 0,
    'ldap_lists_added': 0,
    'ldap_memberships_added': 0,
    'ldap_lists_removed': 0,
    'ldap_memberships_removed': 0
}

# logging
logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
log_file = os.environ.get('SYNC_TARGETS_LOG_FILE')
if log_file:
    ch = logging.handlers.RotatingFileHandler(log_file, mode='a', maxBytes=10485760, backupCount=10)
else:
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
        for key in ('sms', 'call'):
            try:
                users[user['name']][key] = normalize_phone_number(users[user['name']][key])
            except (NumberParseException, KeyError, AttributeError):
                users[user['name']][key] = None

    return users


def prune_user(engine, username):
    metrics.incr('users_purged')

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
        metrics.incr('sql_errors')


def fetch_teams_from_oncall(oncall_base_url):
    try:
        return requests.get('%s/api/v0/teams?fields=name' % oncall_base_url).json()
    except (ValueError, requests.exceptions.RequestException):
        logger.exception('Failed hitting oncall endpoint to fetch list of team names')
        return []


def fix_user_contacts(contacts):
    try:
        contacts['slack'] = contacts.pop('im')
    except KeyError:
        pass

    try:
        contacts['sms'] = normalize_phone_number(contacts['sms'])
    except KeyError:
        pass

    try:
        contacts['call'] = normalize_phone_number(contacts['call'])
    except KeyError:
        pass

    return contacts


def fetch_users_from_oncall(oncall_base_url):

    try:
        return {user['name']: fix_user_contacts(user['contacts']) for user in requests.get('%s/api/v0/users?fields=name&fields=contacts&fields=active' % oncall_base_url).json() if user['active']}
    except (ValueError, KeyError, requests.exceptions.RequestException):
        logger.exception('Failed hitting oncall endpoint to fetch list of users')
        return {}


def sync_from_oncall(config, engine, purge_old_users=True):
    # users and teams present in our oncall database
    oncall_base_url = config.get('oncall-api')

    if not oncall_base_url:
        logger.error('Missing URL to oncall-api, which we use for user/team lookups. Bailing.')
        return

    oncall_users = fetch_users_from_oncall(oncall_base_url)

    if not oncall_users:
        logger.warning('No users found. Bailing.')
        return

    oncall_team_names = fetch_teams_from_oncall(oncall_base_url)

    if not oncall_team_names:
        logger.warning('We do not have a list of team names')

    oncall_team_names = set(oncall_team_names)

    session = sessionmaker(bind=engine)()

    # users present in iris' database
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

    # users from the oncall endpoints and config files
    metrics.set('users_found', len(oncall_users))
    metrics.set('teams_found', len(oncall_team_names))
    oncall_users.update(get_predefined_users(config))
    oncall_usernames = oncall_users.viewkeys()

    # set of users not presently in iris
    users_to_insert = oncall_usernames - iris_usernames
    # set of existing iris users that are in the user oncall database
    users_to_update = iris_usernames & oncall_usernames
    users_to_mark_inactive = iris_usernames - oncall_usernames

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
            metrics.incr('users_failed_to_add')
            metrics.incr('sql_errors')
            logger.exception('Failed to add user %s' % username)
            continue
        metrics.incr('users_added')
        for key, value in oncall_users[username].iteritems():
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
            oncall_contacts = oncall_users[username]
            for mode in modes:
                if mode in oncall_contacts and oncall_contacts[mode]:
                    if mode in db_contacts:
                        if oncall_contacts[mode] != db_contacts[mode]:
                            logger.info('%s: updating %s' % (username, mode))
                            metrics.incr('user_contacts_updated')
                            engine.execute(contact_update_sql, (oncall_contacts[mode], username, modes[mode]))
                    else:
                        logger.info('%s: adding %s' % (username, mode))
                        metrics.incr('user_contacts_updated')
                        engine.execute(contact_insert_sql, (username, modes[mode], oncall_contacts[mode]))
                elif mode in db_contacts:
                    logger.info('%s: deleting %s' % (username, mode))
                    metrics.incr('user_contacts_updated')
                    engine.execute(contact_delete_sql, (username, modes[mode]))
                else:
                    logger.debug('%s: missing %s' % (username, mode))
        except SQLAlchemyError as e:
            metrics.incr('users_failed_to_update')
            metrics.incr('sql_errors')
            logger.exception('Failed to update user %s' % username)
            continue

    # sync teams between iris and oncall
    teams_to_insert = oncall_team_names - iris_team_names

    logger.info('Teams to insert (%d)' % len(teams_to_insert))
    for t in teams_to_insert:
        logger.info('Inserting %s' % t)
        try:
            target_id = engine.execute(target_add_sql, (t, target_types['team'])).lastrowid
            metrics.incr('teams_added')
        except SQLAlchemyError as e:
            logger.exception('Error inserting team %s: %s' % (t, e))
            metrics.incr('teams_failed_to_add')
            continue
    session.commit()
    session.close()

    # mark users inactive
    if purge_old_users:
        logger.info('Users to mark inactive (%d)' % len(users_to_mark_inactive))
        for username in users_to_mark_inactive:
            prune_user(engine, username)


def get_ldap_lists(l, search_strings, parent_list=None):
    results = set()
    known_ldap_resp_ctrls = {
        SimplePagedResultsControl.controlType: SimplePagedResultsControl,
    }
    req_ctrl = SimplePagedResultsControl(True, size=ldap_pagination_size, cookie='')

    if parent_list:
        filterstr = search_strings['get_all_sub_lists_filter'] % escape_filter_chars(parent_list)
    else:
        filterstr = search_strings['get_all_lists_filter']

    while True:
        msgid = l.search_ext(search_strings['list_search_string'],
                             ldap.SCOPE_SUBTREE,
                             serverctrls=[req_ctrl],
                             attrlist=(search_strings['list_cn_field'], search_strings['list_name_field']),
                             filterstr=filterstr)
        rtype, rdata, rmsgid, serverctrls = l.result3(msgid, resp_ctrl_classes=known_ldap_resp_ctrls)

        results |= {(data[search_strings['list_cn_field']][0], data[search_strings['list_name_field']][0]) for (dn, data) in rdata}

        pctrls = [c for c in serverctrls
                  if c.controlType == SimplePagedResultsControl.controlType]

        cookie = pctrls[0].cookie
        if not cookie:
            break
        req_ctrl.cookie = cookie

    return results


def get_ldap_list_membership(l, search_strings, list_name):
    results = set()
    known_ldap_resp_ctrls = {
        SimplePagedResultsControl.controlType: SimplePagedResultsControl,
    }
    req_ctrl = SimplePagedResultsControl(True, size=ldap_pagination_size, cookie='')
    while True:
        msgid = l.search_ext(search_strings['user_search_string'],
                             ldap.SCOPE_SUBTREE,
                             serverctrls=[req_ctrl],
                             attrlist=[search_strings['user_account_name_field']],
                             filterstr=search_strings['user_membership_filter'] % escape_filter_chars(list_name)
                             )
        rtype, rdata, rmsgid, serverctrls = l.result3(msgid, resp_ctrl_classes=known_ldap_resp_ctrls)

        results |= {data[1][search_strings['user_account_name_field']][0] for data in rdata}

        pctrls = [c for c in serverctrls
                  if c.controlType == SimplePagedResultsControl.controlType]

        cookie = pctrls[0].cookie
        if not cookie:
            break
        req_ctrl.cookie = cookie

    return results


def get_ldap_flat_membership(l, search_strings, list_name, max_depth, depth=0, seen_lists=set()):
    members = get_ldap_list_membership(l, search_strings, list_name)

    new_depth = depth + 1
    if new_depth <= max_depth:
        for sub_list, email in get_ldap_lists(l, search_strings, list_name):
            if sub_list in seen_lists:
                logger.warning('avoiding nested list loop with already seen list: %s', sub_list)
                continue
            else:
                seen_lists.add(sub_list)
            sub_list_members = get_ldap_flat_membership(l, search_strings, sub_list, max_depth, new_depth, seen_lists)
            logger.info('Found %s from %s (depth %s/%s)', len(sub_list_members), email, new_depth, max_depth)
            members |= sub_list_members

    return members


def batch_items_from_list(items, items_per_batch):
    items = list(items)
    pos = 0
    while True:
        new_pos = pos + items_per_batch
        items_this_batch = items[pos:new_pos]
        pos = new_pos
        if not items_this_batch:
            break
        yield items_this_batch


def batch_remove_ldap_memberships(session, list_id, members):
    # Remove these in chunks to avoid a gigantic 'where ID in (..)'
    # query that has thousands of entries.
    deletes_per_match = 50
    for memberships_this_batch in batch_items_from_list(members, deletes_per_match):
        affected = session.execute('''DELETE FROM `mailing_list_membership`
                                      WHERE `list_id` = :list_id
                                      AND `user_id` IN (SELECT `id` FROM `target` WHERE `name` IN :members)''',
                                   {'list_id': list_id, 'members': tuple(memberships_this_batch)}).rowcount
        logger.info('Deleted %s members from list id %s', affected, list_id)
    session.commit()


def batch_remove_ldap_lists(session, list_names):
    # Remove these in chunks to avoid a gigantic 'where ID in (..)'
    # query that has thousands of entries.
    deletes_per_match = 50
    for lists_this_batch in batch_items_from_list(list_names, deletes_per_match):
        affected = session.execute('''DELETE FROM `mailing_list`
                                      WHERE `name` IN :list_names''',
                                   {'list_names': tuple(lists_this_batch)}).rowcount

        logger.info('Deleted %s old mailing lists', affected)
    session.commit()


def sync_ldap_lists(ldap_settings, engine):
    try:
        l = ldap.initialize(ldap_settings['connection']['url'])
    except Exception:
        logger.exception('Connecting to ldap to get our mailing lists failed.')
        return

    try:
        l.simple_bind_s(*ldap_settings['connection']['bind_args'])
    except Exception:
        logger.exception('binding to ldap to get our mailing lists failed.')
        return

    session = sessionmaker(bind=engine)()

    ldap_add_pause_interval = ldap_settings.get('user_add_pause_interval', None)
    ldap_add_pause_duration = ldap_settings.get('user_add_pause_duration', 1)

    ldap_lists = get_ldap_lists(l, ldap_settings['search_strings'])
    ldap_lists_count = len(ldap_lists)
    metrics.set('ldap_lists_found', ldap_lists_count)
    metrics.set('ldap_memberships_found', 0)
    logger.info('Found %s ldap lists', ldap_lists_count)

    existing_ldap_lists = {row[0] for row in session.execute('''SELECT `name` FROM `mailing_list`''')}
    kill_lists = existing_ldap_lists - {item[1] for item in ldap_lists}
    if kill_lists:
        metrics.incr('ldap_lists_removed', len(kill_lists))
        batch_remove_ldap_lists(session, kill_lists)

    user_add_count = 0

    for list_cn, list_name in ldap_lists:
        members = get_ldap_flat_membership(l, ldap_settings['search_strings'], list_cn, ldap_settings['max_depth'], 0, set())

        if not members:
            logger.info('Ignoring/pruning empty ldap list %s', list_name)
            continue

        metrics.incr('ldap_memberships_found', len(members))

        list_id = session.execute('''SELECT `id` FROM `mailing_list` WHERE `name` = :name''', {'name': list_name}).scalar()

        if not list_id:
            list_id = session.execute('''INSERT INTO `mailing_list` (`name`) VALUES (:name)''', {'name': list_name}).lastrowid
            session.commit()
            logger.info('Created list %s with id %s', list_name, list_id)
            metrics.incr('ldap_lists_added')

        existing_members = {row[0] for row in session.execute('''
                            SELECT `target`.`name`
                            FROM `mailing_list_membership`
                            JOIN `target` ON `target`.`id` = `mailing_list_membership`.`user_id`
                            WHERE `mailing_list_membership`.`list_id` = :list_id''', {'list_id': list_id})}

        add_members = members - existing_members
        kill_members = existing_members - members

        if add_members:
            metrics.incr('ldap_memberships_added', len(add_members))

            for member in add_members:
                try:
                    session.execute('''INSERT IGNORE INTO `mailing_list_membership`
                                       (`list_id`, `user_id`)
                                       VALUES (:list_id, (SELECT `id` FROM `target` WHERE `name` = :name))''', {'list_id': list_id, 'name': member})
                    logger.info('Added %s to %s', member, list_name)
                except (IntegrityError, DataError):
                    logger.exception('Failed adding %s to %s', member, list_name)

                user_add_count += 1
                if (ldap_add_pause_interval is not None) and (user_add_count % ldap_add_pause_interval) == 0:
                    logger.info('Pausing for %s seconds every %s users.', ldap_add_pause_duration, ldap_add_pause_interval)
                    time.sleep(ldap_add_pause_duration)

        if kill_members:
            metrics.incr('ldap_memberships_removed', len(kill_members))
            batch_remove_ldap_memberships(session, list_id, kill_members)

    session.commit()
    session.close()


def main():
    config = load_config()
    metrics.init(config, 'iris-sync-targets', stats_reset)

    default_nap_time = 3600

    try:
        nap_time = int(config.get('sync_script_nap_time', default_nap_time))
    except ValueError:
        nap_time = default_nap_time

    engine = create_engine(config['db']['conn']['str'] % config['db']['conn']['kwargs'],
                           **config['db']['kwargs'])

    # Optionally, maintain an internal list of mailing lists from ldap that can also be
    # used as targets.
    ldap_lists = config.get('ldap_lists')

    # Initialize these to zero at the start of the app, and don't reset them at every
    # metrics interval
    metrics.set('users_found', 0)
    metrics.set('teams_found', 0)

    metrics.set('ldap_lists_found', 0)
    metrics.set('ldap_memberships_found', 0)

    metrics_task = spawn(metrics.emit_forever)

    while True:
        if not bool(metrics_task):
            logger.error('metrics task failed, %s', metrics_task.exception)
            metrics_task = spawn(metrics.emit_forever)

        sync_from_oncall(config, engine)

        # Do ldap mailing list sync *after* we do the normal sync, to ensure we have the users
        # which will be in ldap already populated.
        if ldap_lists:
            list_run_start = time.time()
            sync_ldap_lists(ldap_lists, engine)
            logger.info('Ldap mailing list sync took %.2f seconds', time.time() - list_run_start)

        logger.info('Sleeping for %d seconds' % nap_time)
        sleep(nap_time)


if __name__ == '__main__':
    main()
