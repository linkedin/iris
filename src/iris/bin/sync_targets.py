# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from gevent import monkey, sleep, spawn
monkey.patch_all()  # NOQA

import logging
import logging.handlers
import os
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DataError
import requests
import oncallclient
from phonenumbers import format_number, parse, PhoneNumberFormat
from phonenumbers.phonenumberutil import NumberParseException

from iris.api import load_config
from iris import metrics

# Used for the optional ldap mailing list resolving functionality
import ldap
from ldap.controls import SimplePagedResultsControl
from ldap.filter import escape_filter_chars
import time
ldap_pagination_size = 1000
ldap_timeout = None

logging.getLogger('requests').setLevel(logging.WARNING)


stats_reset = {
    'sql_errors': 0,
    'users_added': 0,
    'users_failed_to_add': 0,
    'users_failed_to_update': 0,
    'users_purged': 0,
    'others_purged': 0,
    'teams_added': 0,
    'teams_failed_to_add': 0,
    'user_contacts_updated': 0,
    'ldap_lists_added': 0,
    'ldap_memberships_added': 0,
    'ldap_lists_removed': 0,
    'ldap_memberships_removed': 0,
    'ldap_lists_failed_to_add': 0,
    'ldap_memberships_failed_to_add': 0,
    'ldap_reconnects': 0
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

pidfile = os.environ.get('SYNC_TARGETS_PIDFILE')
if pidfile:
    try:
        pid = os.getpid()
        with open(pidfile, 'w') as h:
            h.write('%s\n' % pid)
            logger.info('Wrote pid %s to %s', pid, pidfile)
    except IOError:
        logger.exception('Failed writing pid to %s', pidfile)


def normalize_phone_number(num):
    return format_number(parse(num, 'US'),
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


def prune_target(engine, target_name, target_type):
    if target_type == 'user':
        metrics.incr('users_purged')
    else:
        metrics.incr('others_purged')

    if target_type == 'team':
        try:
            # rename team to prevent namespace conflict but preserve the ability to reactivate it in the future
            new_name = str(uuid.uuid4())
            engine.execute('''UPDATE `target` SET `active` = FALSE, `name` = %s WHERE `name` = %s AND `type_id` = (SELECT `id` FROM `target_type` WHERE `name` = %s)''', (new_name, target_name, target_type))
            logger.info('Deleted inactive oncall team %s', target_name)
        except SQLAlchemyError as e:
            logger.error('Deleting oncall team %s failed: %s', target_name, e)
            metrics.incr('sql_errors')
        return

    try:
        engine.execute('''DELETE FROM `target` WHERE `name` = %s AND `type_id` = (SELECT `id` FROM `target_type` WHERE `name` = %s)''', (target_name, target_type))
        logger.info('Deleted inactive target %s', target_name)

    # The user has messages or some other user data which should be preserved.
    # Just mark as inactive.
    except IntegrityError:
        logger.info('Marking target %s inactive', target_name)
        engine.execute('''UPDATE `target` SET `active` = FALSE WHERE `name` = %s AND `type_id` = (SELECT `id` FROM `target_type` WHERE `name` = %s)''', (target_name, target_type))

    except SQLAlchemyError as e:
        logger.error('Deleting target %s failed: %s', target_name, e)
        metrics.incr('sql_errors')
        return


def fetch_teams_from_oncall(oncall):
    try:
        return oncall.get('%steams?fields=name&active=1&get_id=1' % oncall.url).json()
    except (ValueError, requests.exceptions.RequestException):
        logger.exception('Failed hitting oncall endpoint to fetch list of team names')
        return []


def fix_user_contacts(contacts):
    sms = contacts.get('sms')
    if sms:
        contacts['sms'] = normalize_phone_number(sms)

    call = contacts.get('call')
    if call:
        contacts['call'] = normalize_phone_number(call)

    return contacts


def fetch_users_from_oncall(oncall):
    oncall_user_endpoint = oncall.url + 'users?fields=name&fields=contacts&fields=active'
    try:
        return {user['name']: fix_user_contacts(user['contacts'])
                for user in oncall.get(oncall_user_endpoint).json()
                if user['active']}
    except (ValueError, KeyError, requests.exceptions.RequestException):
        logger.exception('Failed hitting oncall endpoint to fetch list of users')
        return {}


def sync_from_oncall(config, engine, purge_old_users=True):
    # users and teams present in our oncall database
    oncall_base_url = config.get('oncall-api')

    if not oncall_base_url:
        logger.error('Missing URL to oncall-api, which we use for user/team lookups. Bailing.')
        return

    oncall = oncallclient.OncallClient(config.get('oncall-app', ''), config.get('oncall-key', ''), oncall_base_url)
    oncall_users = fetch_users_from_oncall(oncall)

    if not oncall_users:
        logger.warning('No users found. Bailing.')
        return

    # get teams from oncall-api and separate the list of tuples into two lists of name and ids
    oncall_teams_api_response = fetch_teams_from_oncall(oncall)
    if not oncall_teams_api_response:
        logger.warning('No teams found. Bailing.')
        return

    oncall_team_response = list(zip(*oncall_teams_api_response))
    oncall_team_names = oncall_team_response[0]
    oncall_team_ids = oncall_team_response[1]
    oncall_response_dict_name_key = dict(zip(oncall_team_names, oncall_team_ids))
    oncall_response_dict_id_key = dict(zip(oncall_team_ids, oncall_team_names))

    if not oncall_team_names:
        logger.warning('We do not have a list of team names')

    oncall_team_names = set(oncall_team_names)
    oncall_team_ids = set(oncall_team_ids)

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

    iris_usernames = iris_users.keys()

    # users from the oncall endpoints and config files
    metrics.set('users_found', len(oncall_users))
    metrics.set('teams_found', len(oncall_team_names))
    oncall_users.update(get_predefined_users(config))
    oncall_usernames = oncall_users.keys()

    # set of users not presently in iris
    users_to_insert = oncall_usernames - iris_usernames
    # set of existing iris users that are in the user oncall database
    users_to_update = iris_usernames & oncall_usernames
    users_to_mark_inactive = iris_usernames - oncall_usernames

    # get objects needed for insertion
    target_types = {name: target_id for name, target_id in session.execute('SELECT `name`, `id` FROM `target_type`')}  # 'team' and 'user'
    modes = {name: mode_id for name, mode_id in session.execute('SELECT `name`, `id` FROM `mode`')}
    iris_team_names = {name for (name, ) in engine.execute('''SELECT `name` FROM `target` WHERE `type_id` = %s''', target_types['team'])}
    target_add_sql = 'INSERT INTO `target` (`name`, `type_id`) VALUES (%s, %s) ON DUPLICATE KEY UPDATE `active` = TRUE'
    oncall_add_sql = 'INSERT INTO `oncall_team` (`target_id`, `oncall_team_id`) VALUES (%s, %s)'
    user_add_sql = 'INSERT IGNORE INTO `user` (`target_id`) VALUES (%s)'
    target_contact_add_sql = '''INSERT INTO `target_contact` (`target_id`, `mode_id`, `destination`)
                                VALUES (%s, %s, %s)
                                ON DUPLICATE KEY UPDATE `destination` = %s'''

    # insert users that need to be
    logger.info('Users to insert (%d)', len(users_to_insert))
    for username in users_to_insert:
        logger.info('Inserting %s', username)
        try:
            target_id = engine.execute(target_add_sql, (username, target_types['user'])).lastrowid
            engine.execute(user_add_sql, (target_id, ))
        except SQLAlchemyError as e:
            metrics.incr('users_failed_to_add')
            metrics.incr('sql_errors')
            logger.exception('Failed to add user %s' % username)
            continue
        metrics.incr('users_added')
        for key, value in oncall_users[username].items():
            if value and key in modes:
                logger.info('%s: %s -> %s', username, key, value)
                engine.execute(target_contact_add_sql, (target_id, modes[key], value, value))

    # update users that need to be
    contact_update_sql = 'UPDATE target_contact SET destination = %s WHERE target_id = (SELECT id FROM target WHERE name = %s AND type_id = %s) AND mode_id = %s'
    contact_insert_sql = 'INSERT INTO target_contact (target_id, mode_id, destination) VALUES ((SELECT id FROM target WHERE name = %s AND type_id = %s), %s, %s)'
    contact_delete_sql = 'DELETE FROM target_contact WHERE target_id = (SELECT id FROM target WHERE name = %s AND type_id = %s) AND mode_id = %s'

    logger.info('Users to update (%d)', len(users_to_update))
    for username in users_to_update:
        try:
            db_contacts = iris_users[username]
            oncall_contacts = oncall_users[username]
            for mode in modes:
                if mode in oncall_contacts and oncall_contacts[mode]:
                    if mode in db_contacts:
                        if oncall_contacts[mode] != db_contacts[mode]:
                            logger.info('%s: updating %s', username, mode)
                            metrics.incr('user_contacts_updated')
                            engine.execute(contact_update_sql, (oncall_contacts[mode], username, target_types['user'], modes[mode]))
                    else:
                        logger.info('%s: adding %s', username, mode)
                        metrics.incr('user_contacts_updated')
                        engine.execute(contact_insert_sql, (username, target_types['user'], modes[mode], oncall_contacts[mode]))
                elif mode in db_contacts:
                    logger.info('%s: deleting %s', username, mode)
                    metrics.incr('user_contacts_updated')
                    engine.execute(contact_delete_sql, (username, target_types['user'], modes[mode]))
                else:
                    logger.debug('%s: missing %s', username, mode)
        except SQLAlchemyError as e:
            metrics.incr('users_failed_to_update')
            metrics.incr('sql_errors')
            logger.exception('Failed to update user %s', username)
            continue

# sync teams between iris and oncall

    # iris_db_oncall_team_ids (team_ids in the oncall_team table)
    # oncall_team_ids (team_ids from oncall api call)
    # oncall_team_names (names from oncall api call)
    # oncall_response_dict_name_key (key value pairs of oncall team names and ids from api call)
    # oncall_response_dict_id_key same as above but key value inverted
    # iris_team_names (names from target table)
    # iris_target_name_id_dict dictionary of target name -> target_id mappings
    # iris_db_oncall_team_id_name_dict dictionary of oncall team_id -> oncall name mappings

# get all incoming names that match a target check if that target has an entry in oncall table if not make one
    iris_target_name_id_dict = {name: target_id for name, target_id in engine.execute('''SELECT `name`, `id` FROM `target` WHERE `type_id` = %s''', target_types['team'])}

    matching_target_names = iris_team_names.intersection(oncall_team_names)
    if matching_target_names:
        existing_up_to_date_oncall_teams = {name for (name, ) in session.execute('''SELECT `target`.`name` FROM `target` JOIN `oncall_team` ON `oncall_team`.`target_id` = `target`.`id` WHERE `target`.`name` IN :matching_names''', {'matching_names': tuple(matching_target_names)})}
        # up to date target names that don't have an entry in the oncall_team table yet
        matching_target_names_no_oncall_entry = matching_target_names - existing_up_to_date_oncall_teams

        for t in matching_target_names_no_oncall_entry:
            logger.info('Inserting existing team into oncall_team %s', t)
            try:
                engine.execute('''UPDATE `target` SET `active` = TRUE WHERE `id` = %s''', iris_target_name_id_dict[t])
                engine.execute(oncall_add_sql, (iris_target_name_id_dict[t], oncall_response_dict_name_key[t]))
            except SQLAlchemyError as e:
                logger.exception('Error inserting oncall_team %s: %s', t, e)
                continue

# rename all mismatching target names

    iris_db_oncall_team_id_name_dict = {team_id: name for name, team_id in engine.execute('''SELECT target.name, oncall_team.oncall_team_id FROM `target` JOIN `oncall_team` ON oncall_team.target_id = target.id''')}

    iris_db_oncall_team_ids = {oncall_team_id for (oncall_team_id, ) in engine.execute('''SELECT `oncall_team_id` FROM `oncall_team`''')}
    matching_oncall_ids = oncall_team_ids.intersection(iris_db_oncall_team_ids)

    name_swaps = {}

    # find teams in the iris database whose names have changed
    for oncall_id in matching_oncall_ids:

        current_name = iris_db_oncall_team_id_name_dict[oncall_id]
        new_name = oncall_response_dict_id_key[oncall_id]
        if current_name != new_name:
            # handle edge case of teams swapping names
            if not iris_target_name_id_dict.get(new_name, None):
                target_id_to_rename = iris_target_name_id_dict[current_name]
                logger.info('Renaming team %s to %s', current_name, new_name)
                engine.execute('''UPDATE `target` SET `name` = %s, `active` = TRUE WHERE `id` = %s''', (new_name, target_id_to_rename))
            else:
                # there is a team swap so rename to a random name to prevent a violation of unique target name constraint
                new_name = str(uuid.uuid4())
                target_id_to_rename = iris_target_name_id_dict[current_name]
                name_swaps[oncall_id] = target_id_to_rename
                logger.info('Renaming team %s to %s', current_name, new_name)
                engine.execute('''UPDATE `target` SET `name` = %s, `active` = TRUE WHERE `id` = %s''', (new_name, target_id_to_rename))

    # go back and rename name_swaps to correct value
    for oncall_id, target_id_to_rename in name_swaps.items():
        new_name = oncall_response_dict_id_key[oncall_id]
        engine.execute('''UPDATE `target` SET `name` = %s, `active` = TRUE WHERE `id` = %s''', (new_name, target_id_to_rename))


# create new entries for new teams

    # if the team_id doesn't exist in oncall_team at this point then it is a new team.
    new_team_ids = oncall_team_ids - iris_db_oncall_team_ids
    logger.info('Teams to insert (%d)' % len(new_team_ids))

    for team_id in new_team_ids:
        t = oncall_response_dict_id_key[team_id]
        new_target_id = None

        # add team to target table
        logger.info('Inserting %s', t)
        try:
            new_target_id = engine.execute(target_add_sql, (t, target_types['team'])).lastrowid
            metrics.incr('teams_added')
        except SQLAlchemyError as e:
            logger.exception('Error inserting team %s: %s', t, e)
            metrics.incr('teams_failed_to_add')
            continue

        # add team to oncall_team table
        if new_target_id:
            logger.info('Inserting new team into oncall_team %s', t)
            try:
                engine.execute(oncall_add_sql, (new_target_id, team_id))
            except SQLAlchemyError as e:
                logger.exception('Error inserting oncall_team %s: %s', t, e)
                continue

    session.commit()
    session.close()

    # mark users/teams inactive
    if purge_old_users:
        # find active teams that don't exist in oncall anymore
        updated_iris_team_names = {name for (name, ) in engine.execute('''SELECT `name` FROM `target` WHERE `type_id` = %s AND `active` = TRUE''', target_types['team'])}
        teams_to_deactivate = updated_iris_team_names - oncall_team_names

        logger.info('Users to mark inactive (%d)' % len(users_to_mark_inactive))
        for username in users_to_mark_inactive:
            prune_target(engine, username, 'user')
        for team in teams_to_deactivate:
            prune_target(engine, team, 'team')


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
        rtype, rdata, rmsgid, serverctrls = l.result3(msgid, timeout=ldap_timeout, resp_ctrl_classes=known_ldap_resp_ctrls)

        for (dn, data) in rdata:
            cn_field = data[search_strings['list_cn_field']][0]
            name_field = data[search_strings['list_name_field']][0]

            if isinstance(cn_field, bytes):
                cn_field = cn_field.decode('utf-8')
            if isinstance(name_field, bytes):
                name_field = name_field.decode('utf-8')

            results |= {(cn_field, name_field)}

        pctrls = [c for c in serverctrls
                  if c.controlType == SimplePagedResultsControl.controlType]

        if not pctrls:
            # Paging not supported
            break
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
                             attrlist=[search_strings['user_mail_field']],
                             filterstr=search_strings['user_membership_filter'] % escape_filter_chars(list_name)
                             )
        rtype, rdata, rmsgid, serverctrls = l.result3(msgid, timeout=ldap_timeout, resp_ctrl_classes=known_ldap_resp_ctrls)

        for data in rdata:
            member = data[1].get(search_strings['user_mail_field'], [None])[0]
            if isinstance(member, bytes):
                member = member.decode('utf-8')
            results |= {member}

        pctrls = [c for c in serverctrls
                  if c.controlType == SimplePagedResultsControl.controlType]

        if not pctrls:
            # Paging not supported
            break
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
        affected = session.execute('''DELETE `mailing_list_membership`
                                      FROM `mailing_list_membership`
                                      JOIN `target_contact` ON `target_contact`.`target_id` = `mailing_list_membership`.`user_id`
                                      WHERE `list_id` = :list_id
                                      AND `target_contact`.`mode_id` = (SELECT `id` FROM `mode` WHERE `name` = 'email')
                                      AND `destination` IN :members''',
                                   {'list_id': list_id, 'members': tuple(memberships_this_batch)}).rowcount
        logger.info('Deleted %s members from list id %s', affected, list_id)
    session.commit()


def sync_ldap_lists(ldap_settings, engine):
    try:
        if 'cert_path' in ldap_settings:
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_ALLOW)
        l = ldap.ldapobject.ReconnectLDAPObject(ldap_settings['connection']['url'])
    except Exception:
        logger.exception('Connecting to ldap to get our mailing lists failed.')
        return

    try:
        if 'cert_path' in ldap_settings:
            l.set_option(ldap.OPT_X_TLS_CACERTFILE, ldap_settings['cert_path'])
        l.simple_bind_s(*ldap_settings['connection']['bind_args'])
    except Exception:
        logger.exception('binding to ldap to get our mailing lists failed.')
        return

    session = sessionmaker(bind=engine)()

    mailing_list_type_name = 'mailing-list'

    list_type_id = session.execute('SELECT `id` FROM `target_type` WHERE `name` = :name', {'name': mailing_list_type_name}).scalar()
    if not list_type_id:
        try:
            list_type_id = session.execute('INSERT INTO `target_type` (`name`) VALUES (:name)', {'name': mailing_list_type_name}).lastrowid
            session.commit()
            logger.info('Created target_type "%s" with id %s', mailing_list_type_name, list_type_id)
        except (IntegrityError, DataError):
            logger.exeption('Failed creating mailing-list type ID')
            return

    ldap_add_pause_interval = ldap_settings.get('user_add_pause_interval', None)
    ldap_add_pause_duration = ldap_settings.get('user_add_pause_duration', 1)

    ldap_lists = get_ldap_lists(l, ldap_settings['search_strings'])
    ldap_lists_count = len(ldap_lists)
    metrics.set('ldap_lists_found', ldap_lists_count)
    metrics.set('ldap_memberships_found', 0)
    logger.info('Found %s ldap lists', ldap_lists_count)

    existing_ldap_lists = {row[0] for row in session.execute('''SELECT `name` FROM `target` WHERE `target`.`type_id` = :type_id''', {'type_id': list_type_id})}
    kill_lists = existing_ldap_lists - {item[1] for item in ldap_lists}
    if kill_lists:
        metrics.incr('ldap_lists_removed', len(kill_lists))
        for ldap_list in kill_lists:
            prune_target(engine, ldap_list, mailing_list_type_name)

    user_add_count = 0

    for list_cn, list_name in ldap_lists:
        try:
            members = get_ldap_flat_membership(l, ldap_settings['search_strings'], list_cn, ldap_settings['max_depth'], 0, set())
        except ldap.SERVER_DOWN:
            # reconnect and retry once
            metrics.incr('ldap_reconnects')
            logger.warning('LDAP server went away for list %s. Reconnecting', list_name)
            l.reconnect(ldap_settings['connection']['url'])
            members = get_ldap_flat_membership(l, ldap_settings['search_strings'], list_cn, ldap_settings['max_depth'], 0, set())

        if not members:
            logger.info('Ignoring/pruning empty ldap list %s', list_name)
            continue

        num_members = len(members)
        metrics.incr('ldap_memberships_found', num_members)

        created = False
        list_id = session.execute('''SELECT `mailing_list`.`target_id`
                                     FROM `mailing_list`
                                     JOIN `target` on `target`.`id` = `mailing_list`.`target_id`
                                     WHERE `target`.`name` = :name''', {'name': list_name}).scalar()

        if not list_id:
            try:
                list_id = session.execute('''INSERT INTO `target` (`type_id`, `name`)
                                             VALUES (:type_id, :name)''', {'type_id': list_type_id, 'name': list_name}).lastrowid
                session.commit()
            except (IntegrityError, DataError):
                logger.exception('Failed adding row to target table for mailing list %s. Skipping this list.', list_name)
                metrics.incr('ldap_lists_failed_to_add')
                continue

            try:
                session.execute('''INSERT INTO `mailing_list` (`target_id`, `count`) VALUES (:list_id, :count)''', {'list_id': list_id, 'count': num_members})
                session.commit()
            except (IntegrityError, DataError):
                logger.exception('Failed adding row to mailing_list table for mailing list %s (ID: %s). Skipping this list.', list_name, list_id)
                metrics.incr('ldap_lists_failed_to_add')
                continue

            logger.info('Created list %s with id %s', list_name, list_id)
            metrics.incr('ldap_lists_added')
            created = True

        if not created:
            session.execute('UPDATE `mailing_list` SET `count` = :count WHERE `target_id` = :list_id', {'count': num_members, 'list_id': list_id})
            session.commit()

        existing_members = {row[0] for row in session.execute('''
                            SELECT `target_contact`.`destination`
                            FROM `mailing_list_membership`
                            JOIN `target_contact` ON `target_contact`.`target_id` = `mailing_list_membership`.`user_id`
                            WHERE `mailing_list_membership`.`list_id` = :list_id
                            AND `target_contact`.`mode_id` = (SELECT `id` FROM `mode` WHERE `name` = 'email')
                            ''', {'list_id': list_id})}

        add_members = members - existing_members
        kill_members = existing_members - members

        if add_members:
            metrics.incr('ldap_memberships_added', len(add_members))

            for member in add_members:
                try:
                    session.execute('''INSERT IGNORE INTO `mailing_list_membership`
                                       (`list_id`, `user_id`)
                                       VALUES (:list_id,
                                               (SELECT `target_id` FROM `target_contact`
                                                JOIN `target` ON `target`.`id` = `target_id`
                                                WHERE `destination` = :name
                                                AND `mode_id` = (SELECT `id` FROM `mode` WHERE `name` = 'email')
                                                AND `target`.`type_id` = (SELECT `id` FROM `target_type` WHERE `name` = 'user')))
                                    ''', {'list_id': list_id, 'name': member})
                    logger.info('Added %s to list %s', member, list_name)
                except (IntegrityError, DataError):
                    metrics.incr('ldap_memberships_failed_to_add')
                    logger.warning('Failed adding %s to %s', member, list_name)

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
    global ldap_timeout
    config = load_config()
    metrics.init(config, 'iris-sync-targets', stats_reset)

    default_ldap_timeout = 20
    default_nap_time = 3600

    ldap_timeout = int(config.get('sync_script_ldap_timeout', default_ldap_timeout))
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

            if 'ldap_cert_path' in ldap_lists:
                ldap_cert_path = ldap_lists['ldap_cert_path']
                if not os.access(ldap_cert_path, os.R_OK):
                    logger.error("Failed to read ldap_cert_path certificate")
                    raise IOError
                else:
                    ldap_lists['cert_path'] = ldap_cert_path
            list_run_start = time.time()
            sync_ldap_lists(ldap_lists, engine)
            logger.info('Ldap mailing list sync took %.2f seconds', time.time() - list_run_start)

        logger.info('Sleeping for %d seconds' % nap_time)
        sleep(nap_time)


if __name__ == '__main__':
    main()
