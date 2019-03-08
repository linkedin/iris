# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from time import time
from gevent import spawn, sleep
from gevent.lock import Semaphore
from collections import deque
from datetime import datetime
import iris.cache
from iris import metrics
import logging
import ujson

logger = logging.getLogger(__name__)

get_application_quotas_query = '''SELECT `application`.`name` as application,
                                         `application_quota`.`hard_quota_threshold`,
                                         `application_quota`.`soft_quota_threshold`,
                                         `application_quota`.`hard_quota_duration`,
                                         `application_quota`.`soft_quota_duration`,
                                         `target`.`name` as target_name,
                                         `target_type`.`name` as target_role,
                                         `application_quota`.`plan_name`,
                                         `application_quota`.`wait_time`
                                 FROM `application_quota`
                                 JOIN `application` ON `application`.`id` = `application_quota`.`application_id`
                                 LEFT JOIN `target` on `target`.`id` = `application_quota`.`target_id`
                                 LEFT JOIN `target_type` on `target_type`.`id` = `target`.`type_id` '''

insert_application_quota_query = '''INSERT INTO `application_quota` (`application_id`, `hard_quota_threshold`,
                                                                     `soft_quota_threshold`, `hard_quota_duration`,
                                                                     `soft_quota_duration`, `plan_name`,
                                                                     `target_id`, `wait_time`)
                                    VALUES (:application_id, :hard_quota_threshold, :soft_quota_threshold,
                                            :hard_quota_duration, :soft_quota_duration, :plan_name, :target_id, :wait_time)
                                    ON DUPLICATE KEY UPDATE `hard_quota_threshold` = :hard_quota_threshold,
                                                            `soft_quota_threshold` = :soft_quota_threshold,
                                                            `hard_quota_duration` = :hard_quota_duration,
                                                            `soft_quota_duration` = :soft_quota_duration,
                                                            `plan_name` = :plan_name,
                                                            `target_id` = :target_id,
                                                            `wait_time` = :wait_time'''

create_incident_query = '''INSERT INTO `incident` (`plan_id`, `created`, `context`, `current_step`, `active`, `application_id`)
                           VALUES ((SELECT `plan_id` FROM `plan_active` WHERE `name` = :plan_name),
                                   :created, :context, 0, TRUE, :sender_app_id)'''

check_incident_claimed_query = '''SELECT `active` FROM `incident` WHERE `id` = :id'''

required_quota_keys = frozenset(['hard_quota_threshold', 'soft_quota_threshold',
                                 'hard_quota_duration', 'soft_quota_duration',
                                 'plan_name', 'wait_time', 'target_name'])

quota_int_keys = ('hard_quota_threshold', 'soft_quota_threshold',
                  'hard_quota_duration', 'soft_quota_duration', 'wait_time')

soft_quota_notification_interval = 1800


class ApplicationQuota(object):

    def __init__(self, db, expand_targets, message_send_enqueue, sender_app):
        self.db = db
        self.expand_targets = expand_targets
        self.message_send_enqueue = message_send_enqueue
        self.iris_application = None
        if sender_app:
            self.iris_application = iris.cache.applications.get(sender_app)
            if self.iris_application:
                logger.info('Using iris application (%s) for sender quota notifications.', sender_app)
            else:
                logger.error('Invalid iris application (%s) used for sender. Quota breach notificiations/incidents will not work.', sender_app)
        else:
            logger.warning('Iris sender_app not configured so notifications for quota breaches will not work')

        self.rates = {}  # application: (hard_buckets, soft_buckets, hard_limit, soft_limit, wait_time, plan_name, (target_name, target_role))
        self.last_incidents = {}  # application: (incident_id, time())
        self.last_incidents_mutex = Semaphore()
        self.last_soft_quota_notification_time = {}  # application: time()
        self.last_soft_quota_notification_time_mutex = Semaphore()
        metrics.add_new_metrics({'quota_hard_exceed_cnt': 0, 'quota_soft_exceed_cnt': 0})
        spawn(self.refresh)

    def get_new_rules(self):
        session = self.db.Session()
        for row in session.execute(get_application_quotas_query):
            yield row
        session.close()

    def refresh(self):
        while True:
            logger.info('Refreshing app quotas')
            new_rates = {}

            for application, hard_limit, soft_limit, hard_duration, soft_duration, target_name, target_role, plan_name, wait_time in self.get_new_rules():
                new_rates[application] = (hard_limit, soft_limit, hard_duration // 60, soft_duration // 60, wait_time, plan_name, (target_name, target_role))

            old_keys = self.rates.keys()
            new_keys = new_rates.keys()

            # Remove old application entries
            for key in old_keys - new_keys:
                logger.info('Pruning old application quota for %s', key)
                try:
                    del(self.rates[key])
                    del(self.last_incidents[key])
                except KeyError:
                    pass

            # Create new ones with fresh buckets
            for key in new_keys - old_keys:
                hard_limit, soft_limit, hard_duration, soft_duration, wait_time, plan_name, target = new_rates[key]
                self.rates[key] = (deque([0] * hard_duration, maxlen=hard_duration),  # hard buckets
                                   deque([0] * soft_duration, maxlen=soft_duration),  # soft buckets
                                   hard_limit, soft_limit, wait_time, plan_name, target)

            # Update existing ones + append new time interval. Keep same time bucket object if duration hasn't changed, otherwise create new
            # one and resize accordingly
            for key in new_keys & old_keys:
                hard_limit, soft_limit, hard_duration, soft_duration, wait_time, plan_name, target = new_rates[key]
                self.rates[key] = (self.rates[key][0] if len(self.rates[key][0]) == hard_duration else deque(self.rates[key][0], maxlen=hard_duration),
                                   self.rates[key][1] if len(self.rates[key][1]) == soft_duration else deque(self.rates[key][1], maxlen=soft_duration),
                                   hard_limit, soft_limit, wait_time, plan_name, target)

                # Increase minute interval for hard + soft buckets
                self.rates[key][0].append(0)
                self.rates[key][1].append(0)

            metrics.add_new_metrics({'app_%s_quota_%s_usage_pct' % (app, quota_type): 0 for quota_type in ('hard', 'soft') for app in new_keys})

            logger.info('Refreshed app quotas: %s', ', '.join(new_keys))
            sleep(60)

    def allow_send(self, message):
        application = message.get('application')

        if not application:
            return True

        # Purpose of quotas is to protect downstreams. If we're already going to drop this message,
        # don't let it account against quota.
        if message.get('mode') == 'drop':
            return True

        rate = self.rates.get(application)

        if not rate:
            return True

        hard_buckets, soft_buckets, hard_limit, soft_limit, wait_time, plan_name, target = rate

        # Increment both buckets for this minute
        hard_buckets[-1] += 1
        soft_buckets[-1] += 1

        # If hard limit breached, disallow sending this message and create incident
        hard_quota_usage = sum(hard_buckets)

        hard_usage_pct = 0
        if hard_limit > 0:
            hard_usage_pct = (hard_quota_usage // hard_limit) * 100
        metrics.set('app_%s_quota_hard_usage_pct' % application, hard_usage_pct)

        if hard_quota_usage > hard_limit:
            metrics.incr('quota_hard_exceed_cnt')
            with self.last_incidents_mutex:
                self.notify_incident(application, hard_limit, len(hard_buckets), plan_name, wait_time)
            return False

        # If soft limit breached, just notify owner and still send
        soft_quota_usage = sum(soft_buckets)

        soft_usage_pct = 0
        if soft_limit > 0:
            soft_usage_pct = (soft_quota_usage // soft_limit) * 100
        metrics.set('app_%s_quota_soft_usage_pct' % application, soft_usage_pct)

        if soft_quota_usage > soft_limit:
            metrics.incr('quota_soft_exceed_cnt')
            with self.last_soft_quota_notification_time_mutex:
                self.notify_target(application, soft_limit, len(soft_buckets), *target)
            return True

        return True

    def notify_incident(self, application, limit, duration, plan_name, wait_time):
        if not self.iris_application:
            logger.warning('Application %s breached hard quota. Cannot notify owners as application is not set', application)
            return

        if not plan_name:
            logger.error('Application %s breached hard quota. Cannot create iris incident as plan is not set (may have been deleted).', application)
            return

        logger.warning('Application %s breached hard quota. Will create incident using plan %s', application, plan_name)

        session = self.db.Session()

        # Avoid creating new incident if we have an incident that's either not claimed or claimed and wait_time hasn't been exceeded
        last_incident = self.last_incidents.get(application)
        if last_incident:
            last_incident_id, last_incident_created = last_incident
            claimed = session.execute(check_incident_claimed_query, {'id': last_incident_id}).scalar()

            if claimed:
                logger.info('Skipping creating incident for application %s as existing incident %s is not claimed', application, last_incident_id)
                session.close()
                return

            if wait_time and (time() - last_incident_created) < wait_time:
                logger.info('Skipping creating incident for application %s as it is not yet %s seconds since existing incident %s was claimed',
                            application, wait_time, last_incident_id)
                session.close()
                return

        # Make a new incident
        incident_data = {
            'plan_name': plan_name,
            'created': datetime.utcnow(),
            'sender_app_id': self.iris_application['id'],
            'context': ujson.dumps({
                'quota_breach': {
                    'application': application,
                    'limit': limit,
                    'duration': duration
                }
            })
        }

        incident_id = session.execute(create_incident_query, incident_data).lastrowid

        session.commit()
        session.close()

        self.last_incidents[application] = incident_id, time()
        logger.info('Created incident %s', incident_id)

    def notify_target(self, application, limit, duration, target_name, target_role):
        if not self.iris_application:
            logger.warning('Application %s breached soft quota. Cannot notify owners as application is not set', application)
            return

        if not target_name or not target_role:
            logger.error('Application %s breached soft quota. Cannot notify owner as they aren\'t set (may have been deleted).', application)
            return

        last_notification_time = self.last_soft_quota_notification_time.get(application)

        now = time()
        if last_notification_time is not None and (now - last_notification_time) < soft_quota_notification_interval:
            logger.warning('Application %s breached soft quota. Will NOT notify %s:%s as they will only get a notification once every %s seconds.',
                           application, target_role, target_name, soft_quota_notification_interval)
            return

        self.last_soft_quota_notification_time[application] = now

        logger.warning('Application %s breached soft quota. Will notify %s:%s', application, target_role, target_name)

        targets = self.expand_targets(target_role, target_name)

        if not targets:
            logger.error('Failed resolving %s:%s to notify soft quota breach.', target_role, target_name)
            return

        mode_id = iris.cache.modes.get('email')

        if not mode_id:
            logger.error('Failed resolving email mode to notify soft quota breach for application %s', application)
            return

        for username in targets:
            message = {
                'application': self.iris_application['name'],
                'mode_id': mode_id,
                'mode': 'email',
                'target': username,
                'subject': 'Application %s exceeding message quota' % application,
                'body': ('Hi %s\n\nYour application %s is currently exceeding its soft quota of %s messages per %s minutes.\n\n'
                         'If this continues, your messages will eventually be dropped on the floor and an Iris incident will be raised.\n\n'
                         'Regards,\nIris') % (username, application, limit, duration, )
            }
            self.message_send_enqueue(message)
