# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from kazoo.client import KazooClient, KazooState
from kazoo.handlers.gevent import SequentialGeventHandler
from kazoo.recipe.party import Party
import kazoo.exceptions
import logging
from iris import metrics
from gevent import sleep
from itertools import cycle

logger = logging.getLogger(__name__)

UPDATE_FREQUENCY = 3


class Coordinator(object):
    def __init__(self, zk_hosts, hostname, port, join_cluster):
        self.me = '%s:%s' % (hostname, port)
        self.is_leader = None
        self.followers = cycle([])
        self.follower_count = 0
        self.started_shutdown = False

        if join_cluster:
            read_only = False
        else:
            read_only = True

        self.zk = KazooClient(hosts=zk_hosts, handler=SequentialGeventHandler(), read_only=read_only)
        event = self.zk.start_async()
        event.wait(timeout=5)

        self.lock = self.zk.Lock(path='/iris/sender_leader', identifier=self.me)

        # Used to keep track of followers / senders present in cluster
        self.party = Party(client=self.zk, path='/iris/sender_nodes', identifier=self.me)

        if join_cluster:
            self.zk.add_listener(self.event_listener)
            self.party.join()

    def am_i_leader(self):
        return self.is_leader

    # Used for API to get the current leader
    def get_current_leader(self):
        try:
            contenders = self.lock.contenders()
        except kazoo.exceptions.KazooException:
            logger.exception('Failed getting contenders')
            return None

        if contenders:
            return self.address_to_tuple(contenders[0])
        else:
            return None

    # Used for API to get the current followers if leader can't be reached
    def get_current_followers(self):
        return [self.address_to_tuple(host) for host in self.party]

    def address_to_tuple(self, address):
        try:
            host, port = address.split(':')
            return host, int(port)
        except (IndexError, ValueError):
            logger.error('Failed getting address tuple from %s', address)
            return None

    def update_status(self):
        if self.started_shutdown:
            return

        if self.zk.state == KazooState.CONNECTED:
            if self.lock.is_acquired:
                self.is_leader = True
            else:
                try:
                    self.is_leader = self.lock.acquire(blocking=False, timeout=2)

                # This one is expected when we're recovering from ZK being down
                except kazoo.exceptions.CancelledError:
                    self.is_leader = False

                except kazoo.exceptions.LockTimeout:
                    self.is_leader = False
                    logger.exception('Failed trying to acquire lock (shouldn\'t happen as we\'re using nonblocking locks)')

                except kazoo.exceptions.KazooException:
                    self.is_leader = False
                    logger.exception('ZK problem while Failed trying to acquire lock')
        else:
            logger.error('ZK connection is in %s state', self.zk.state)
            self.is_leader = False

        if self.zk.state == KazooState.CONNECTED:

            if self.is_leader:
                followers = [self.address_to_tuple(host) for host in self.party if host != self.me]
                self.follower_count = len(followers)
                self.followers = cycle(followers)
            else:
                self.followers = cycle([])
                self.follower_count = 0

            # Keep us as part of the party, so the current leader sees us as a follower
            if not self.party.participating:
                try:
                    self.party.join()
                except kazoo.exceptions.KazooException:
                    logger.exception('ZK problem while trying to join party')
        else:
            self.followers = cycle([])
            self.follower_count = 0

    def update_forever(self):
        while True:
            if self.started_shutdown:
                return

            old_status = self.is_leader
            self.update_status()
            new_status = self.is_leader

            if old_status != new_status:
                log = logger.info
            else:
                log = logger.debug

            if self.is_leader:
                log('I am the leader sender')
            else:
                log('I am a follower sender')

            metrics.set('follower_instance_count', self.follower_count)
            metrics.set('is_leader_sender', int(self.is_leader is True))

            sleep(UPDATE_FREQUENCY)

    def leave_cluster(self):
        self.started_shutdown = True

        # cancel any attempts to acquire leader lock which could make us hang
        self.lock.cancel()

        if self.zk.state == KazooState.CONNECTED:
            if self.party and self.party.participating:
                logger.info('Leaving party')
                self.party.leave()
            if self.lock and self.lock.is_acquired:
                logger.info('Releasing lock')
                self.lock.release()

        # Make us not the leader
        self.is_leader = False

        # Avoid sending metrics that we are still the leader when we're not
        metrics.set('is_leader_sender', 0)

    def event_listener(self, state):
        if state == KazooState.LOST or state == KazooState.SUSPENDED:
            logger.info('ZK state transitioned to %s. Resetting leader status.', state)

            # cancel pending attempts to acquire lock which will break and leave
            # us in bad state
            self.lock.cancel()

            # make us try to re-acquire lock during next iteration when we're connected
            if self.lock.is_acquired:
                self.lock.is_acquired = False

            # make us try to rejoin the party during next iteration when we're connected
            if self.party.participating:
                self.party.participating = False

            # in the meantime we're not leader
            self.is_leader = None
