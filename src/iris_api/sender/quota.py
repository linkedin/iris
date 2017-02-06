# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from time import time
from gevent import spawn, sleep
from collections import deque
from datetime import datetime
from iris_api.sender.shared import send_queue
from iris_api.cache import priorities, applications
from iris_api.metrics import stats
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
                                 JOIN `target` on `target`.`id` = `application_quota`.`target_id`
                                 JOIN `target_type` on `target_type`.`id` = `target`.`type_id` '''

create_incident_query = '''INSERT INTO `incident` (`plan_id`, `created`, `context`, `current_step`, `active`, `application_id`)
                           VALUES ((SELECT `plan_id` FROM `plan_active` WHERE `name` = :plan_name),
                                   :created, :context, 0, TRUE, :sender_app_id)'''

check_incident_claimed_query = '''SELECT `active` FROM `incident` WHERE `id` = :id'''


class ApplicationQuota(object):

    def __init__(self, db, expand_targets, sender_app):
        self.db = db
        self.expand_targets = expand_targets
        self.iris_application = None
        if sender_app:
            self.iris_application = applications.get(sender_app)
            if not self.iris_application:
                logger.error('Invalid iris application (%s) used for sender. Quota breach notificiations/incidents will not work.', sender_app)

        self.rates = {}  # application: (hard_buckets, soft_buckets, hard_limit, soft_limit, wait_time, plan_name, (target_name, target_role))
        self.last_incidents = {}  # application: (incident_id, time())
        spawn(self.refresh)

    def refresh(self):
        while True:
            logger.info('Refreshing app quotas')
            new_rates = {}

            session = self.db.Session()
            data = session.execute(get_application_quotas_query)

            for application, hard_limit, soft_limit, hard_duration, soft_duration, target_name, target_role, plan_name, wait_time in data:
                new_rates[application] = (hard_limit, soft_limit, hard_duration / 60, soft_duration / 60, wait_time, plan_name, (target_name, target_role))

            session.close()

            old_keys = self.rates.viewkeys()
            new_keys = new_rates.viewkeys()

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

            logger.info('Refreshed app quotas: %s', ', '.join(new_keys))
            sleep(60)

    def allow_send(self, message):
        application = message.get('application')

        if not application:
            return True

        rate = self.rates.get(application)

        if not rate:
            return True

        hard_buckets, soft_buckets, hard_limit, soft_limit, wait_time, plan_name, target = rate

        # Increment both buckets for this minute
        hard_buckets[-1] += 1
        soft_buckets[-1] += 1

        # If hard limit breached, disallow sending this message and create incident
        if sum(hard_buckets) > hard_limit:
            stats['quota_hard_exceed_cnt'] += 1
            self.notify_incident(application, hard_limit, len(hard_buckets), plan_name, wait_time)
            return False

        # If soft limit breached, just notify owner and still send
        if sum(soft_buckets) > soft_limit:
            stats['quota_soft_exceed_cnt'] += 1
            self.notify_target(application, soft_limit, len(soft_buckets), *target)
            return True

        return True

    def notify_incident(self, application, limit, duration, plan_name, wait_time):
        if not self.iris_application:
            logger.warning('Application %s breached hard quota. Cannot notify owners as application is not set')
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
            'quota-breach': {
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
            logger.warning('Application %s breached soft quota. Cannot notify owners as application is not set')
            return

        logger.warning('Application %s breached soft quota. Will notify %s:%s', application, target_role, target_name)

        targets = self.expand_targets(target_role, target_name)

        if not targets:
            logger.error('Failed resolving %s:%s to notify soft quota breach.', target_role, target_name)
            return

        priority = priorities.get('low')

        if not priority:
            logger.error('Failed resolving low priority to notify soft quota breach')

        for username in targets:
            message = {
              'application': self.iris_application['name'],
              'priority_id': priority['id'],
              'target': username,
              'subject': 'Application %s exceeding message quota' % application,
              'body': ('Hi %s\n\nYour application %s is currently exceeding its soft quota of %s messages per %s minutes.\n\n'
                       'If this continues, your messages will eventually be dropped on the floor and an Iris incident will be raised.\n\n'
                       'Regards,\nIris') % (username, application, limit, duration, )
            }
            send_queue.put(message)
