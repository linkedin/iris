# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from itertools import cycle
import logging
logger = logging.getLogger(__name__)


class Coordinator():
    def __init__(self, is_master, slaves=[]):
        self.is_master = is_master
        if is_master:
            logger.info('I am the master sender')
        else:
            logger.info('I am a slave sender')

        self.slaves = cycle((slave['host'], slave['port']) for slave in slaves)
        self.slave_count = len(slaves)

    def update_forever(self):
        pass

    def leave_cluster(self):
        pass

    def am_i_master(self):
        return self.is_master
