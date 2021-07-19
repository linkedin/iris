# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from .. import db
from gevent import sleep
import logging
logger = logging.getLogger(__name__)

MODE_CHANGE = 'mode-change'
TARGET_CHANGE = 'target-change'
SENT_CHANGE = 'sent-change'
CONTENT_CHANGE = 'content-change'


def message_change(message_id, change_type, old, new, description):
    if not message_id:
        logger.warning('Not logging %s for message as it does not have an id', change_type)
        return

    old = old[0:250]
    new = new[0:250]
    description = description[0:250]

    # retry to guard against deadlocks
    retries = 0
    max_retries = 5
    while True:
        with db.guarded_session() as session:
            retries += 1
            try:
                session.execute('''
                  INSERT INTO `message_changelog` (`message_id`, `change_type`, `old`, `new`, `description`, `date`)
                  VALUES (:message_id, :change_type, :old, :new, :description, NOW())
                ''', dict(message_id=message_id, change_type=change_type, old=old, new=new, description=description))
                session.commit()
                session.close()
            except Exception:
                logger.exception('Failed inserting message into auditlog. (Try %s/%s)', retries, max_retries)
                if retries < max_retries:
                    sleep(.2)
                    continue
                else:
                    raise Exception('Failed inserting message into auditlog retries exceeded')
            else:
                logger.info('Logged change information for message (ID %s)', message_id)
                break
