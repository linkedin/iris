import time
from datetime import datetime
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


def calculate_app_stats(app, connection, cursor, fields_filter=None):
    queries = {
        'total_incidents': 'SELECT COUNT(*) FROM `incident` WHERE `created` < %(date_variable)s AND `application_id` = %(application_id)s',
        'total_messages_sent': 'SELECT COUNT(*) FROM `message` WHERE `sent` < %(date_variable)s AND `application_id` = %(application_id)s',
        'total_incidents_last_week': 'SELECT COUNT(*) FROM `incident` WHERE `created` > %(date_variable)s - INTERVAL 1 WEEK AND `created` < %(date_variable)s AND `application_id` = %(application_id)s',
        'total_messages_sent_last_week': 'SELECT COUNT(*) FROM `message` USE INDEX (ix_message_sent) WHERE `sent` > %(date_variable)s - INTERVAL 1 WEEK AND `sent` < %(date_variable)s AND `application_id` = %(application_id)s',
        'pct_incidents_claimed_last_week': '''SELECT ROUND(COUNT(`owner_id`) / COUNT(*) * 100, 2)
                                               FROM `incident`
                                               WHERE `created` > %(date_variable)s - INTERVAL 1 WEEK
                                               AND `created` < %(date_variable)s
                                               AND `application_id` = %(application_id)s''',
        'median_seconds_to_claim_last_week': '''SELECT @incident_count := (SELECT count(*)
                                                                            FROM `incident`
                                                                            WHERE `created` > %(date_variable)s - INTERVAL 1 WEEK
                                                                            AND `created` < %(date_variable)s
                                                                            AND `active` = FALSE
                                                                            AND NOT ISNULL(`owner_id`)
                                                                            AND NOT ISNULL(`updated`)
                                                                            AND `application_id` = %(application_id)s),
                                                                    @row_id := 0,
                                                                    (SELECT CEIL(AVG(time_to_claim)) AS median
                                                                    FROM (SELECT `updated` - `created` AS time_to_claim
                                                                          FROM `incident`
                                                                          WHERE `created` > %(date_variable)s - INTERVAL 1 WEEK
                                                                          AND `created` < %(date_variable)s
                                                                          AND `active` = FALSE
                                                                          AND NOT ISNULL(`owner_id`)
                                                                          AND NOT ISNULL(`updated`)
                                                                          AND `application_id` = %(application_id)s
                                                                          ORDER BY time_to_claim) AS time_to_claim
                                                                    WHERE (SELECT @row_id := @row_id + 1)
                                                                    BETWEEN @incident_count/2.0 AND @incident_count/2.0 + 1)''',
        'total_call_retry_last_week': '''SELECT COUNT(*)
                                          FROM `twilio_retry` JOIN `message` ON `message`.`id` = `twilio_retry`.`message_id`
                                          WHERE `sent` > %(date_variable)s - INTERVAL 1 WEEK
                                          AND `sent` < %(date_variable)s
                                          AND `application_id` = %(application_id)s''',

        'high_priority_incidents_last_week': '''SELECT application.name, COUNT(DISTINCT incident.application_id, incident.id) as incident_count
                                                        FROM incident JOIN application ON application.id = %(application_id)s JOIN message ON message.incident_id = incident.id AND application.id = incident.application_id
                                                        WHERE incident.created > %(date_variable)s - INTERVAL 1 WEEK AND incident.created < %(date_variable)s AND priority_id IN (SELECT id FROM priority WHERE name IN ("high","urgent"))
                                                        GROUP BY incident.application_id ORDER BY incident_count DESC'''

    }

    mode_status = defaultdict(lambda: defaultdict(int))

    mode_stats_types = {
        'sms': {
            'fail': ['undelivered'],
            'success': ['sent', 'delivered']
        },
        'call': {
            'success': ['completed'],
            'fail': ['failed']
        },
        'email': {
            'success': [1],
            'fail': [0],
        }
    }

    cursor.execute('SELECT `name` FROM `mode`')
    modes = [row[0] for row in cursor]
    stats = {}
    fields = queries.keys()
    if fields_filter:
        fields &= set(fields_filter)

    for delta in range(0, 7):
        # 3600 seconds in an hour, round down to the nearest hour
        # 604800 seconds in a week, shift date by delta number of weeks
        unix_date = int(time.time() // 3600 * 3600) - (delta * 604800)
        now = datetime.fromtimestamp(unix_date)
        formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
        query_data = {'application_id': app['id'], 'date_variable': formatted_date}

        for key in fields:
            start = time.time()
            cursor.execute(queries[key], query_data)
            result = cursor.fetchone()
            if result:
                result = result[-1]

            logger.info('Stats query %s took %s seconds', key, round(time.time() - start, 2))

            # {statistic : {timestamp: value, timestamp: value}}
            if stats.get(key):
                stats[key].append({unix_date: result})
            else:
                stats[key] = []
                stats[key].append({unix_date: result})

        start = time.time()

        cursor.execute('''SELECT `mode`.`name`, COALESCE(`generic_message_sent_status`.`status`, `twilio_delivery_status`.`status`) AS thisStatus,
                            COUNT(*) FROM `message` USE INDEX FOR JOIN (ix_message_created)
                        LEFT JOIN `twilio_delivery_status` ON `twilio_delivery_status`.`message_id` = `message`.`id`
                        LEFT JOIN `generic_message_sent_status` ON `generic_message_sent_status`.`message_id` = `message`.`id`
                        JOIN `mode` ON `mode`.`id` = `message`.`mode_id`
                        WHERE ((NOT ISNULL(`twilio_delivery_status`.`status`) AND `mode`.`name` != 'email') OR (NOT ISNULL(`generic_message_sent_status`.`status`) AND `mode`.`name` = 'email'))
                            AND `message`.`application_id` = %(application_id)s
                            AND `message`.`created` > %(date_variable)s - INTERVAL 1 WEEK
                            AND `message`.`created` < %(date_variable)s
                        GROUP BY thisStatus, `mode`.`name`''', query_data)
        logger.info('App Stats (%s) mode status query took %s seconds', app['name'], round(time.time() - start, 2))

        for mode, status, count in cursor:
            if isinstance(status, str) and status.isdigit():
                status = int(status)
            mode_status[mode][status] = count

        for mode in mode_stats_types:
            status_counts = mode_status[mode]
            overall = float(sum(status_counts.values()))
            if overall > 0:
                fail_pct = round(
                    (sum(status_counts.pop(key, 0) for key in mode_stats_types[mode]['fail']) / overall) * 100,
                    2)
                success_pct = round(
                    (sum(status_counts.pop(key, 0) for key in mode_stats_types[mode]['success']) / overall) * 100, 2)
                other_pct = round(sum(status_counts.values()) / overall * 100, 2)
            else:
                fail_pct = success_pct = other_pct = None

            key = 'pct_%s_success_last_week' % mode
            if stats.get(key):
                stats['pct_%s_success_last_week' % mode].append({unix_date: success_pct})
                stats['pct_%s_fail_last_week' % mode].append({unix_date: fail_pct})
                stats['pct_%s_other_last_week' % mode].append({unix_date: other_pct})
            else:
                stats['pct_%s_success_last_week' % mode] = []
                stats['pct_%s_fail_last_week' % mode] = []
                stats['pct_%s_other_last_week' % mode] = []

                stats['pct_%s_success_last_week' % mode].append({unix_date: success_pct})
                stats['pct_%s_fail_last_week' % mode].append({unix_date: fail_pct})
                stats['pct_%s_other_last_week' % mode].append({unix_date: other_pct})

        # Get counts of messages sent per mode
        cursor.execute('''SELECT `mode`.`name`, `msg_count` FROM
                            (SELECT `mode_id`, COUNT(*) AS `msg_count` FROM `message`
                            USE INDEX (ix_message_sent)
                            WHERE `sent` > %(date_variable)s - INTERVAL 1 WEEK
                            AND `sent` < %(date_variable)s
                            AND `application_id` = %(application_id)s
                            GROUP BY `mode_id`) `counts`
                        JOIN `mode` ON `mode`.`id` = `counts`.`mode_id`''',
                       query_data)

        for row in cursor:
            key = 'total_%s_sent_last_week' % row[0]
            result = row[1]

            if stats.get(key):
                stats[key].append({unix_date: result})
            else:
                stats[key] = []
                stats[key].append({unix_date: result})

        # Zero out modes that don't show up in the count
        for mode in modes:
            count_stat = 'total_%s_sent_last_week' % mode
            if count_stat not in stats:
                stats[count_stat] = []
                stats[count_stat].append({unix_date: 0})
            elif unix_date not in stats[count_stat]:
                stats[count_stat].append({unix_date: 0})

    return stats


def calculate_single_stat(connection, cursor, stat_name):

    queries = {
        'total_incidents': 'SELECT application.name, COUNT(*) as cnt FROM `incident` JOIN application ON application.id = incident.application_id WHERE `created` < %(date_variable)s GROUP BY application.name ORDER BY cnt DESC, application.name ASC',
        'total_messages_sent': 'SELECT application.name, COUNT(*) as cnt FROM `message` JOIN application ON application.id = message.application_id WHERE `sent` < %(date_variable)s GROUP BY application.name ORDER BY cnt DESC, application.name ASC',
        'total_incidents_last_week': 'SELECT application.name, COUNT(*) as cnt FROM `incident` JOIN application ON application.id = incident.application_id WHERE `created` > %(date_variable)s - INTERVAL 1 WEEK AND `created` < %(date_variable)s GROUP BY application.name ORDER BY cnt DESC, application.name ASC',
        'total_messages_sent_last_week': 'SELECT application.name, COUNT(*) as cnt FROM `message` USE INDEX (ix_message_sent) JOIN application ON application.id = message.application_id WHERE `sent` > %(date_variable)s - INTERVAL 1 WEEK AND `sent` < %(date_variable)s GROUP BY application.name ORDER BY cnt DESC, application.name ASC',
        'pct_incidents_claimed_last_week': '''SELECT application.name, (ROUND(COUNT(`owner_id`) / COUNT(*) * 100, 2)) as cnt
                                               FROM `incident`
                                               JOIN application ON application.id = incident.application_id
                                               WHERE `created` > %(date_variable)s - INTERVAL 1 WEEK
                                               AND `created` < %(date_variable)s
                                               GROUP BY application.name ORDER BY cnt DESC, application.name ASC''',
        'total_call_retry_last_week': '''SELECT application.name, COUNT(*) as cnt
                                          FROM `twilio_retry` JOIN `message` ON `message`.`id` = `twilio_retry`.`message_id`
                                          JOIN application ON application.id = message.application_id
                                          WHERE `sent` > %(date_variable)s - INTERVAL 1 WEEK
                                          AND `sent` < %(date_variable)s GROUP BY application.name ORDER BY cnt DESC, application.name ASC''',
        'high_priority_incidents_last_week': '''SELECT application.name, COUNT(DISTINCT incident.application_id, incident.id) AS incident_count
                                                FROM incident JOIN application ON application.id = incident.application_id
                                                JOIN message ON message.incident_id = incident.id WHERE incident.created > %(date_variable)s - INTERVAL 1 WEEK
                                                AND incident.created < %(date_variable)s
                                                AND priority_id IN ( SELECT id FROM priority WHERE name IN ('high', 'urgent') )
                                                GROUP BY application.name ORDER BY incident_count DESC, application.name ASC'''

    }

    stats = {}

    for delta in range(0, 7):
        # 3600 seconds in an hour, round down to the nearest hour
        # 604800 seconds in a week, shift date by delta number of weeks
        unix_date = int(time.time() // 3600 * 3600) - (delta * 604800)
        now = datetime.fromtimestamp(unix_date)
        formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
        stats[unix_date] = []

        row_count = cursor.execute(queries[stat_name], {'date_variable': formatted_date})
        if row_count > 0:
            for app_name, count in cursor:
                stats[unix_date].append({app_name: count})

    return stats


def calculate_global_stats(connection, cursor, fields_filter=None):

    queries = {
        'total_plans': 'SELECT COUNT(*) FROM `plan` WHERE `created` <= %(date_variable)s',
        'total_incidents': 'SELECT COUNT(*) FROM `incident` WHERE `created` <= %(date_variable)s',
        'total_messages_sent': 'SELECT COUNT(*) FROM `message` WHERE `sent` <= %(date_variable)s',
        'total_incidents_last_week': 'SELECT COUNT(*) FROM `incident` WHERE `created` > %(date_variable)s - INTERVAL 1 WEEK AND `created` < %(date_variable)s',
        'total_messages_sent_last_week': 'SELECT COUNT(*) FROM `message` WHERE `sent` > %(date_variable)s - INTERVAL 1 WEEK AND `sent` < %(date_variable)s',
        'total_active_users': 'SELECT COUNT(*) FROM `target` WHERE `type_id` = (SELECT `id` FROM `target_type` WHERE `name` = "user") AND `active` = TRUE',
        'pct_incidents_claimed_last_week': '''SELECT ROUND(
                                                (SELECT COUNT(*) FROM `incident`
                                                WHERE `created` > (%(date_variable)s - INTERVAL 1 WEEK)
                                                AND `created` < (%(date_variable)s)
                                                AND `active` = FALSE
                                                AND NOT isnull(`owner_id`)) /
                                                (SELECT COUNT(*) FROM `incident`
                                                WHERE `created` > (%(date_variable)s - INTERVAL 1 WEEK)
                                                AND `created` < (%(date_variable)s)) * 100, 2)''',
        'median_seconds_to_claim_last_week': '''SELECT @incident_count := (SELECT count(*)
                                                                            FROM `incident`
                                                                            WHERE `created` > (%(date_variable)s - INTERVAL 1 WEEK)
                                                                            AND `created` < (%(date_variable)s)
                                                                            AND `active` = FALSE
                                                                            AND NOT ISNULL(`owner_id`)
                                                                            AND NOT ISNULL(`updated`)),
                                                        @row_id := 0,
                                                        (SELECT CEIL(AVG(time_to_claim)) as median
                                                        FROM (SELECT `updated` - `created` as time_to_claim
                                                                FROM `incident`
                                                                WHERE `created` > (%(date_variable)s - INTERVAL 1 WEEK)
                                                                AND `created` < (%(date_variable)s)
                                                                AND `active` = FALSE
                                                                AND NOT ISNULL(`owner_id`)
                                                                AND NOT ISNULL(`updated`)
                                                                ORDER BY time_to_claim) as time_to_claim
                                                        WHERE (SELECT @row_id := @row_id + 1)
                                                        BETWEEN @incident_count/2.0 AND @incident_count/2.0 + 1)''',
        'total_applications': 'SELECT COUNT(*) FROM `application` WHERE `auth_only` = FALSE',
        'total_high_priority_incidents_last_week': 'SELECT COUNT(DISTINCT incident.id) FROM incident JOIN message ON message.incident_id = incident.id WHERE incident.created > %(date_variable)s - INTERVAL 1 WEEK AND incident.created < %(date_variable)s AND priority_id IN (SELECT id FROM priority WHERE name IN ("high","urgent"))'
    }

    stats = {}
    fields = queries.keys()
    if fields_filter:
        fields &= set(fields_filter)

    for delta in range(0, 7):

        # 3600 seconds in an hour, round down to the nearest hour
        # 604800 seconds in a week, shift date by delta number of weeks
        unix_date = int(time.time() // 3600 * 3600) - (delta * 604800)
        now = datetime.fromtimestamp(unix_date)
        formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')

        for key in fields:
            start = time.time()
            cursor.execute(queries[key], {'date_variable': formatted_date})
            result = cursor.fetchone()
            if result:
                result = result[-1]

            logger.info('Stats query %s took %s seconds', key, round(time.time() - start, 2))

            # format: {statistic : [{timestamp: value}, {timestamp: value}]}
            if key in stats:
                stats[key].append({unix_date: result})
            else:
                stats[key] = []
                stats[key].append({unix_date: result})

    return stats
