# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from iris import db
import logging
logger = logging.getLogger(__name__)


class mailing_list(object):
    def __init__(self, config):
        self.max_list_names = config.get('ldap_lists', {}).get('max_unrolled_users', 0)

    def get(self, role, target):
        if role == 'mailing-list':
            return self.unroll_mailing_list(target)
        else:
            return None

    def unroll_mailing_list(self, list_name):
        connection = db.engine.raw_connection()
        cursor = connection.cursor()
        cursor.execute('''SELECT `target`.`name`
                          FROM `mailing_list_membership`
                          JOIN `target` ON `mailing_list_membership`.`user_id` = `target`.`id`
                          JOIN `mailing_list` ON `mailing_list_membership`.`list_id` = `mailing_list`.`id`
                          WHERE `mailing_list`.`name` = %s''', [list_name])
        names = [row[0] for row in cursor]
        cursor.close()
        connection.close()
        count = len(names)
        if self.max_list_names > 0 and count >= self.max_list_names:
            logger.warn('Not returning any results for list group %s as it contains too many members (%s > %s)',
                        list_name, count, self.max_list_names)
            return None
        else:
            logger.info('Unrolled %s people from list %s', count, list_name)
            return names
