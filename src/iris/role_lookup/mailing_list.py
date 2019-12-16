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

        cursor.execute('''
          SELECT `mailing_list`.`target_id`,
                 `mailing_list`.`count`
          FROM `mailing_list`
          JOIN `target` on `target`.`id` = `mailing_list`.`target_id`
          WHERE `target`.`name` = %s
        ''', list_name)

        list_info = cursor.fetchone()

        if not list_info:
            logger.warning('Invalid mailing list %s', list_name)
            cursor.close()
            connection.close()
            return None

        list_id, list_count = list_info

        if self.max_list_names > 0 and list_count >= self.max_list_names:
            logger.warning('Not returning any results for list group %s as it contains too many members (%s > %s)',
                           list_name, list_count, self.max_list_names)
            cursor.close()
            connection.close()
            return None

        cursor.execute('''SELECT `target`.`name`
                          FROM `mailing_list_membership`
                          JOIN `target` on `target`.`id` = `mailing_list_membership`.`user_id`
                          WHERE `mailing_list_membership`.`list_id` = %s''', [list_id])
        names = [row[0] for row in cursor]

        cursor.close()
        connection.close()

        logger.info('Unfurled %s people from list %s', len(names), list_name)
        return names
