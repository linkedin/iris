# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from gevent import monkey, sleep, spawn
monkey.patch_all()  # NOQA

from sqlalchemy import create_engine
from collections import deque
import logging
import logging.handlers
import ujson
import errno
import time
import os

from iris.api import load_config
from iris import metrics

# metrics
stats_reset = {
    'sql_errors': 0,
    'deleted_messages': 0,
    'deleted_incidents': 0,
    'deleted_comments': 0
}

# logging
logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
log_file = os.environ.get('RETENTION_LOG_FILE')
if log_file:
    ch = logging.handlers.RotatingFileHandler(log_file, mode='a', maxBytes=10485760, backupCount=10)
else:
    ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(ch)


# pidfile
pidfile = os.environ.get('RETENTION_PIDFILE')
if pidfile:
    try:
        pid = os.getpid()
        with open(pidfile, 'w') as h:
            h.write('%s\n' % pid)
            logger.info('Wrote pid %s to %s', pid, pidfile)
    except IOError:
        logger.exception('Failed writing pid to %s', pidfile)

# Avoid using DictCursor; manually handle columns/offsets here, and only create dict
# when time to archive and dump json. XXX: make sure ID is first
incident_fields = (
    ('`incident`.`id`', 'incident_id'),
    ('`incident`.`created`', 'created'),
    ('`incident`.`context`', 'context'),
    ('`incident`.`plan_id`', 'plan_id'),
    ('`plan`.`name`', 'plan_name'),
    ('`application`.`name`', 'application_name'),
    ('`target`.`name`', 'owner'),
)

message_fields = (
    ('`message`.`id`', 'message_id'),
    ('`message`.`incident_id`', 'incident_id'),
    ('`mode`.`name`', 'mode'),
    ('`priority`.`name`', 'priority'),
    ('`target`.`name`', 'target'),
    ('`template`.`name`', 'template'),
    ('`message`.`subject`', 'subject'),
    ('`message`.`template_id`', 'template_id'),
    ('`message`.`body`', 'body'),
    ('`message`.`created`', 'created'),
)

comment_fields = (
    ('`comment`.`id`', 'comment_id'),
    ('`comment`.`incident_id`', 'incident_id'),
    ('`target`.`name`', 'author'),
    ('`comment`.`content`', 'content'),
    ('`comment`.`created`', 'created'),
)


def archive_incident(incident_row, archive_path):
    incident = {field[1]: incident_row[i] for i, field in enumerate(incident_fields)}

    created = incident['created']
    incident_dir = os.path.join(archive_path, str(created.year), str(created.month), str(created.day), str(incident['incident_id']))

    try:
        os.makedirs(incident_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            logger.exception('Failed creating %s DIR', incident_dir)
            return

    incident_file = os.path.join(incident_dir, 'incident_data.json')

    try:
        with open(incident_file, 'w') as handle:
            ujson.dump(incident, handle, indent=2)
    except IOError:
        logger.exception('Failed writing incident metadata to %s', incident_file)


def archive_message(message_row, archive_path):
    message = {field[1]: message_row[i] for i, field in enumerate(message_fields)}

    created = message['created']
    incident_dir = os.path.join(archive_path, str(created.year), str(created.month), str(created.day), str(message['incident_id']))

    try:
        os.makedirs(incident_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            logger.exception('Failed creating %s DIR', incident_dir)
            return

    message_file = os.path.join(incident_dir, 'message_%d.json' % message['message_id'])

    try:
        with open(message_file, 'w') as handle:
            ujson.dump(message, handle, indent=2)
    except IOError:
        logger.exception('Failed writing message to %s', message_file)


def archive_comment(comment_row, archive_path):
    comment = {field[1]: comment_row[i] for i, field in enumerate(comment_fields)}

    created = comment['created']
    incident_dir = os.path.join(archive_path, str(created.year), str(created.month), str(created.day), str(comment['incident_id']))

    try:
        os.makedirs(incident_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            logger.exception('Failed creating %s DIR', incident_dir)
            return

    comment_file = os.path.join(incident_dir, 'comment_%d.json' % comment['comment_id'])

    try:
        with open(comment_file, 'w') as handle:
            ujson.dump(comment, handle, indent=2)
    except IOError:
        logger.exception('Failed writing comment to %s', comment_file)


def process_retention(engine, max_days, batch_size, cooldown_time, archive_path):
    time_start = time.time()

    connection = engine.raw_connection()
    cursor = connection.cursor(engine.dialect.dbapi.cursors.SSCursor)

    deleted_incidents = 0
    deleted_messages = 0
    deleted_comments = 0

    # First, archive/kill incidents and their messages
    while True:

        # Get incidents to archive and kill, in batches
        try:
            cursor.execute(
                '''
                    SELECT
                        %s
                    FROM `incident`
                    LEFT JOIN `plan` on `plan`.`id` = `incident`.`plan_id`
                    LEFT JOIN `application` on `application`.`id` = `incident`.`application_id`
                    LEFT JOIN `target` ON `incident`.`owner_id` = `target`.`id`
                    WHERE `incident`.`created` < (CURDATE() - INTERVAL %%s DAY)
                    LIMIT %%s
                ''' % (', '.join(field[0] for field in incident_fields)),
                [max_days, batch_size])
        except Exception:
            logger.exception('Failed getting incidents')
            try:
                cursor.close()
            except Exception:
                pass
            cursor = connection.cursor(engine.dialect.dbapi.cursors.SSCursor)
            break

        incident_ids = deque()

        for incident in cursor:
            archive_incident(incident, archive_path)
            incident_ids.append(incident[0])

        if not incident_ids:
            break

        logger.info('Archived %d incidents', len(incident_ids))

        # Then, Archive+Kill all comments in these incidents
        while True:

            try:
                cursor.execute(
                    '''
                        SELECT
                          %s
                        FROM `comment`
                        LEFT JOIN `target` ON `comment`.`user_id` = `target`.`id`
                        WHERE `comment`.`incident_id` in %%s
                        LIMIT %%s
                    ''' % (', '.join(field[0] for field in comment_fields)),
                    [tuple(incident_ids), batch_size])

            except Exception:
                metrics.incr('sql_errors')
                logger.exception('Failed getting comments')
                try:
                    cursor.close()
                except Exception:
                    pass
                cursor = connection.cursor(engine.dialect.dbapi.cursors.SSCursor)
                break

            comment_ids = deque()

            for comment in cursor:
                archive_comment(comment, archive_path)
                comment_ids.append(comment[0])

            if not comment_ids:
                break

            logger.info('Archived %d comments', len(comment_ids))

            try:
                deleted_rows = cursor.execute('DELETE FROM `comment` WHERE `id` IN %s', [tuple(comment_ids)])
                connection.commit()
            except Exception:
                metrics.incr('sql_errors')
                logger.exception('Failed deleting comments from incidents')
                try:
                    cursor.close()
                except Exception:
                    pass
                cursor = connection.cursor(engine.dialect.dbapi.cursors.SSCursor)
                break
            else:
                if deleted_rows:
                    logger.info('Killed %d comments from %d incidents', deleted_rows, len(incident_ids))
                    deleted_comments += deleted_rows
                    sleep(cooldown_time)
                else:
                    break

        # Archive+Kill all messages in these incidents
        while True:

            try:
                cursor.execute(
                    '''
                        SELECT
                          %s
                        FROM `message`
                        JOIN `priority` on `priority`.`id` = `message`.`priority_id`
                        LEFT JOIN `mode` on `mode`.`id` = `message`.`mode_id`
                        LEFT JOIN `template` ON `message`.`template_id` = `template`.`id`
                        LEFT JOIN `target` ON `message`.`target_id` = `target`.`id`
                        WHERE `message`.`incident_id` in %%s
                        LIMIT %%s
                    ''' % (', '.join(field[0] for field in message_fields)),
                    [tuple(incident_ids), batch_size])

            except Exception:
                metrics.incr('sql_errors')
                logger.exception('Failed getting messages')
                try:
                    cursor.close()
                except Exception:
                    pass
                cursor = connection.cursor(engine.dialect.dbapi.cursors.SSCursor)
                break

            message_ids = deque()

            for message in cursor:
                archive_message(message, archive_path)
                message_ids.append(message[0])

            if not message_ids:
                break

            logger.info('Archived %d messages', len(message_ids))

            try:
                deleted_rows = cursor.execute('DELETE FROM `message` WHERE `id` IN %s', [tuple(message_ids)])
                connection.commit()
            except Exception:
                metrics.incr('sql_errors')
                logger.exception('Failed deleting messages from incidents')
                try:
                    cursor.close()
                except Exception:
                    pass
                cursor = connection.cursor(engine.dialect.dbapi.cursors.SSCursor)
                break
            else:
                if deleted_rows:
                    logger.info('Killed %d messages from %d incidents', deleted_rows, len(incident_ids))
                    deleted_messages += deleted_rows
                    sleep(cooldown_time)
                else:
                    break

        # Finally kill incidents
        try:
            deleted_rows = cursor.execute('DELETE FROM `incident` WHERE `id` IN %s', [tuple(incident_ids)])
            connection.commit()
        except Exception:
            metrics.incr('sql_errors')
            logger.exception('Failed deleting incidents')
            try:
                cursor.close()
            except Exception:
                pass
            cursor = connection.cursor(engine.dialect.dbapi.cursors.SSCursor)
            break
        else:
            logger.info('Deleted %s incidents', deleted_rows)
            deleted_incidents += deleted_rows
            sleep(cooldown_time)

    # Next, kill messages not tied to incidents, like quota notifs or incident tracking emails
    while True:
        try:
            deleted_rows = cursor.execute('DELETE FROM `message` WHERE `created` < (CURDATE() - INTERVAL %s DAY) AND `incident_id` IS NULL LIMIT %s', [max_days, batch_size])
            connection.commit()
        except Exception:
            metrics.incr('sql_errors')
            logger.exception('Failed deleting messages')
            try:
                cursor.close()
            except Exception:
                pass
            break
        else:
            if deleted_rows:
                logger.info('Killed %d misc messages', deleted_rows)
                deleted_messages += deleted_rows
                sleep(cooldown_time)
            else:
                break

    try:
        cursor.close()
    except Exception:
        pass
    connection.close()

    logger.info('Run took %.2f seconds and deleted %d incidents and %d messages', time.time() - time_start, deleted_incidents, deleted_messages)
    metrics.set('deleted_messages', deleted_messages)
    metrics.set('deleted_incidents', deleted_incidents)
    metrics.set('deleted_comments', deleted_comments)


def main():
    config = load_config()
    metrics.init(config, 'iris-process-retention', stats_reset)

    retention_settings = config.get('retention', {})
    if not retention_settings.get('enabled'):
        logger.info('Retention not enabled, bailing')
        return

    engine = create_engine(config['db']['conn']['str'] % config['db']['conn']['kwargs'],
                           **config['db']['kwargs'])

    max_days = int(retention_settings['max_days'])
    if max_days < 1:
        logger.error('Max days needs to at least be 1')
        return

    cooldown_time = int(retention_settings['cooldown_time'])
    batch_size = int(retention_settings['batch_size'])
    run_interval = int(retention_settings['run_interval'])
    archive_path = retention_settings['archive_path']

    spawn(metrics.emit_forever)

    while True:
        logger.info('Starting retention loop (kill messages+incidents older than %d days)', max_days)
        try:
            process_retention(engine, max_days=max_days, cooldown_time=cooldown_time, batch_size=batch_size, archive_path=archive_path)
        except Exception:
            logger.exception('Hit problem while running retention')
        logger.info('Waiting %d seconds until next iteration..', run_interval)
        sleep(run_interval)
