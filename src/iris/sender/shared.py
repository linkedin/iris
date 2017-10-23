# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from iris.metrics import stats
import logging

logger = logging.getLogger(__name__)

# queue for sending messages. mode -> gevent queue
per_mode_send_queues = {}


def add_mode_stat(mode, runtime):
    try:
        stats[mode + '_cnt'] += 1
        if runtime is None:
            stats[mode + '_fail'] += 1
        else:
            stats[mode + '_total'] += runtime
            stats[mode + '_sent'] += 1
            if runtime > stats[mode + '_max']:
                stats[mode + '_max'] = runtime
            elif runtime < stats[mode + '_min']:
                stats[mode + '_min'] = runtime
            if runtime < stats[mode + '_min']:
                stats[mode + '_min'] = runtime
            elif runtime > stats[mode + '_max']:
                stats[mode + '_max'] = runtime
    except KeyError as e:
        logger.exception('failed modifying nonexistent metric: %s', e)
