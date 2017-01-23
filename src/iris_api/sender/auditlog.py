# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from .. import db
import logging
logger = logging.getLogger(__name__)

MODE_CHANGE = 'mode-change'
TARGET_CHANGE = 'target-change'
SENT_CHANGE = 'sent-change'


def message_change(message_id, change_type, old, new, description):
    if not message_id:
        logger.warn('Not logging %s for message as it does not have an id', change_type)
        return

    session = db.Session()
    session.execute('''
      INSERT INTO `message_changelog` (`message_id`, `change_type`, `old`, `new`, `description`, `date`)
      VALUES (:message_id, :change_type, :old, :new, :description, NOW())
    ''', dict(message_id=message_id, change_type=change_type, old=old, new=new, description=description))
    session.commit()
    session.close()
    logger.info('Logged change information for message (ID %s)', message_id)
