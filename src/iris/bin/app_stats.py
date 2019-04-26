# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from gevent import monkey, sleep, spawn
monkey.patch_all()  # NOQA

import logging
import os

from iris import db, metrics, app_stats
from iris.api import load_config

# logging
logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
log_file = os.environ.get('APP_STATS_LOG_FILE')
if log_file:
    ch = logging.handlers.RotatingFileHandler(log_file, mode='a', maxBytes=10485760, backupCount=10)
else:
    ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(ch)


# pidfile
pidfile = os.environ.get('APP_STATS_PIDFILE')
if pidfile:
    try:
        pid = os.getpid()
        with open(pidfile, 'w') as h:
            h.write('%s\n' % pid)
            logger.info('Wrote pid %s to %s', pid, pidfile)
    except IOError:
        logger.exception('Failed writing pid to %s', pidfile)

stats_reset = {
    'task_failure': 0,
}


def set_global_stats(stats, connection, cursor):
    # delete outdated stats
    cursor.execute('''DELETE FROM `global_stats`''')

    for stat in stats.keys():
        for timestamp, val in stats[stat].items():
            cursor.execute('''INSERT INTO `global_stats` (`statistic`, `value`, `timestamp`)
                            VALUES (%s, %s, %s)
                            ON DUPLICATE KEY UPDATE `value`= %s, `timestamp` = %s''',
                           (stat, val, timestamp, val, timestamp))
    connection.commit()


def set_app_stats(app, stats, connection, cursor):
    for stat in stats.keys():
        for timestamp, val in stats[stat].items():
            cursor.execute('''INSERT INTO `application_stats` (`application_id`, `statistic`, `value`, `timestamp`)
                            VALUES (%s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE `value`= %s, `timestamp` = %s''',
                           (app['id'], stat, val, timestamp, val, timestamp))
    connection.commit()


def stats_task():
    connection = db.engine.raw_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT `id`, `name` FROM `application`')
    applications = [{'id': row[0], 'name': row[1]} for row in cursor]
    # clean up old app stats
    cursor.execute('''DELETE FROM `application_stats`''')
    for app in applications:
        try:
            stats = app_stats.calculate_app_stats(app, connection, cursor)
            set_app_stats(app, stats, connection, cursor)
        except Exception:
            logger.exception('App stats calculation failed for app %s', app['name'])
            metrics.incr('task_failure')
    try:
        stats = app_stats.calculate_global_stats(connection, cursor)
        set_global_stats(stats, connection, cursor)
    except Exception:
        logger.exception('Global stats calculation failed')
        metrics.incr('task_failure')

    cursor.close()
    connection.close()


def main():
    config = load_config()
    metrics.init(config, 'iris-application-stats', stats_reset)
    # app_stats_settings = config.get('app-stats', {})
    # run_interval = int(app_stats_settings['run_interval'])
    spawn(metrics.emit_forever)
    db.init(config)
    run_interval = 300
    while True:
        logger.info('Starting app stats calculation loop')
        stats_task()
        logger.info('Waiting %d seconds until next iteration..', run_interval)
        sleep(run_interval)


if __name__ == '__main__':
    main()
