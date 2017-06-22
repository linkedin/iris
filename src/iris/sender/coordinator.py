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
    def __init__(self, zk_hosts, hostname, port, join_cluster=True):
        self.me = '%s:%s' % (hostname, port)
        self.is_master = None
        self.slaves = cycle([])
        self.slave_count = 0
        self.started_shutdown = False

        self.zk = KazooClient(hosts=zk_hosts, handler=SequentialGeventHandler(), read_only=bool(join_cluster))
        event = self.zk.start_async()
        event.wait(timeout=5)

        self.lock = self.zk.Lock(path='/iris/sender_master', identifier=self.me)

        # Used to keep track of slaves / senders present in cluster
        self.party = Party(client=self.zk, path='/iris/sender_nodes', identifier=self.me)

        if join_cluster:
            self.party.join()

    def am_i_master(self):
        return self.is_master

    # Used for API to get the current master
    def get_current_master(self):
        try:
            contenders = self.lock.contenders()
        except kazoo.exceptions.KazooException:
            logger.exception('Failed getting contenders')
            return None

        if contenders:
            return self.address_to_tuple(contenders[0])
        else:
            return None

    # Used for API to get the current slaves if master can't be reached
    def get_current_slaves(self):
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
            if self.is_master:
                self.is_master = self.lock.is_acquired
            else:
                try:
                    self.is_master = self.lock.acquire(blocking=False, timeout=2)
                except kazoo.exceptions.LockTimeout:
                    self.is_master = False
                    logger.exception('Failed trying to acquire lock (shouldn\'t happen as we\'re using nonblocking locks)')
                except kazoo.exceptions.KazooException:
                    self.is_master = False
                    logger.exception('ZK problem while Failed trying to acquire lock')
        else:
            logger.error('ZK connection is not in connected state')
            self.is_master = False

        if self.is_master:
            slaves = [self.address_to_tuple(host) for host in self.party if host != self.me]
            self.slave_count = len(slaves)
            self.slaves = cycle(slaves)
        else:
            self.slaves = cycle([])
            self.slave_count = 0

    def update_forever(self):
        while True:
            if self.started_shutdown:
                return

            old_status = self.is_master
            self.update_status()
            new_status = self.is_master

            if old_status != new_status:
                log = logger.info
            else:
                log = logger.debug

            if self.is_master:
                log('I am the master sender')
            else:
                log('I am a slave sender')

            metrics.set('slave_instance_count', self.slave_count)
            metrics.set('is_master_sender', int(self.is_master))

            sleep(UPDATE_FREQUENCY)

    def leave_cluster(self):
        self.started_shutdown = True
        if self.party and self.party.participating:
            logger.info('Leaving party')
            self.party.leave()
        if self.lock and self.lock.is_acquired:
            logger.info('Releasing lock')
            self.lock.release()


class NonClusterCoordinator():
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
