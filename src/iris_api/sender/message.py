# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from .. import db
import logging

logger = logging.getLogger(__name__)


def update_message_mode(message):
    if not message.get('message_id'):
        logger.warning('Cannot change mode for message %s as it is missing message_id', message)
        return

    session = db.Session()
    mode_id = session.execute('SELECT `id` FROM `mode` WHERE `name` = :mode', message).scalar()

    # Need to update mode_id in the dictionary as its gets set in DB in other parts of the sender
    if mode_id:
        message['mode_id'] = mode_id
        session.execute('UPDATE `message` SET `mode_id` = :mode_id WHERE `id` = :message_id', message)
        session.commit()
    else:
        logger.warning('Cannot update mode for message %(message_id)s to %(mode)s as looking up its ID failed', message)

    session.close()
