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
from phonenumbers import format_number, parse, PhoneNumberFormat
from phonenumbers.phonenumberutil import NumberParseException

from iris_api.api import load_config_file
from iris_api import metrics

from requests.packages.urllib3.exceptions import (
    InsecureRequestWarning, SNIMissingWarning, InsecurePlatformWarning
)
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


def fetch_teams(oncall_base_url):
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


def fetch_users(oncall_base_url):

    try:
        return {user['name']: fix_user_contacts(user['contacts']) for user in requests.get('%s/api/v0/users?fields=name&fields=contacts' % oncall_base_url).json()}
    except (ValueError, KeyError, requests.exceptions.RequestException):
        logger.exception('Failed hitting oncall endpoint to fetch list of users')
        return {}


def sync(config, engine, purge_old_users=True):
    # users and teams present in our oncall database
    oncall_base_url = config.get('oncall-api')

    if not oncall_base_url:
        logger.error('Missing URL to oncall-api, which we use for user/team lookups. Bailing.')
        return

    oncall_users = fetch_users(oncall_base_url)

    if not oncall_users:
        logger.warning('No users found. Bailing.')
        return

    oncall_team_names = fetch_teams(oncall_base_url)

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


def main():
    config = load_config_file(sys.argv[1])
    metrics.init(config, 'iris-sync-targets', stats_reset)

    default_nap_time = 3600

    try:
        nap_time = int(config.get('sync_script_nap_time', default_nap_time))
    except ValueError:
        nap_time = default_nap_time

    engine = create_engine(config['db']['conn']['str'] % config['db']['conn']['kwargs'],
                           **config['db']['kwargs'])

    # Initialize these to zero at the start of the app, and don't reset them at every
    # metrics interval
    metrics.set('users_found', 0)
    metrics.set('teams_found', 0)

    metrics_task = spawn(metrics.emit_forever)

    while True:
        if not bool(metrics_task):
            logger.error('metrics task failed, %s', metrics_task.exception)
            metrics_task = spawn(metrics.emit_forever)

        sync(config, engine)
        logger.info('Sleeping for %d seconds' % nap_time)
        sleep(nap_time)


if __name__ == '__main__':
    main()
