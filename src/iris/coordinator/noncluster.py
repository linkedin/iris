# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from itertools import cycle
import logging
logger = logging.getLogger(__name__)


class Coordinator():
    def __init__(self, is_leader, followers=[]):
        self.is_leader = is_leader
        if is_leader:
            logger.info('I am the leader sender')
        else:
            logger.info('I am a follower sender')

        self.followers = cycle((follower['host'], follower['port']) for follower in followers)
        self.follower_count = len(followers)

    def update_forever(self):
        pass

    def leave_cluster(self):
        pass

    def am_i_leader(self):
        return self.is_leader

    def get_current_leader(self):
        return None
