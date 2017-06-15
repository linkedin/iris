import logging
from iris import db, metrics
from gevent import sleep, spawn
from itertools import cycle

logger = logging.getLogger(__name__)

UPDATE_FREQUENCY = 3
SENDER_ALIVE_TIMEOUT = 10

REMOVE_OLD_INSTANCES_FREQUENCY = 3600
REMOVE_OLD_INSTANCES_TIMEOUT = 60

GET_MASTER_QUERY = '''SELECT `sender_address` FROM `sender_master_election` WHERE `anchor` = 1'''

GET_SLAVES_QUERY = '''
  SELECT `sender_address`
  FROM `sender_instances`
  WHERE `last_seen` > NOW() - INTERVAL CAST(:timeout AS UNSIGNED) SECOND
  AND `sender_address` NOT IN (%s)''' % GET_MASTER_QUERY

UPDATE_MASTER_QUERY = '''
  INSERT IGNORE INTO `sender_master_election` (`anchor`, `sender_address`, `last_seen_active`) VALUES (
    1, :me, NOW()
  ) ON DUPLICATE KEY UPDATE
    `sender_address` = if(`last_seen_active` < NOW() - INTERVAL CAST(:timeout AS UNSIGNED) SECOND, VALUES(`sender_address`), `sender_address`),
    `last_seen_active` = if(`sender_address` = VALUES(`sender_address`), VALUES(`last_seen_active`), `last_seen_active`)
'''

UPDATE_INSTANCES_QUERY = '''
  INSERT INTO `sender_instances` (`sender_address`, `last_seen`) VALUES(:me, now())
  ON DUPLICATE KEY UPDATE `last_seen` = NOW()'''

REMOVE_OLD_INSTANCES_QUERY = '''
  DELETE FROM `sender_instances`
  WHERE `last_seen` < NOW() - INTERVAL CAST(:old_instances_timeout AS UNSIGNED) SECOND
'''


class Coordinator(object):
    def __init__(self, hostname, port):
        self.me = '%s:%s' % (hostname, port)
        self.is_master = None
        self.slaves = cycle([])
        self.slave_count = 0

        self.prune_old_instances_task = None

    def am_i_master(self):
        return self.is_master

    # Used for API to get the current master
    def get_current_master(self):
        session = db.Session()
        master = session.execute(GET_MASTER_QUERY).scalar()
        session.close()
        return self.address_to_tuple(master)

    # Used for API to get the current slaves if master can't be reached
    def get_current_slaves(self):
        session = db.Session()
        slaves = []
        for row in session.execute(GET_SLAVES_QUERY, {'timeout': SENDER_ALIVE_TIMEOUT}):
            address = self.address_to_tuple(row[0])
            if address:
                slaves.append(address)
        session.close()
        return slaves

    def address_to_tuple(self, address):
        try:
            host, port = address.split(':', 1)
            return host, int(port)
        except (IndexError, ValueError):
            logger.error('Failed getting address tuple from %s', address)
            return None

    def update_status(self):
        session = db.Session()

        try:
            session.execute(UPDATE_MASTER_QUERY, {'me': self.me, 'timeout': SENDER_ALIVE_TIMEOUT})
            session.commit()
        except:
            logger.exception('Failed updating master status')

        self.is_master = session.execute(GET_MASTER_QUERY).scalar() == self.me

        # Keep track of slaves if we're master
        if self.is_master:
            slaves = []
            for row in session.execute(GET_SLAVES_QUERY, {'timeout': SENDER_ALIVE_TIMEOUT}):
                address = self.address_to_tuple(row[0])
                if address:
                    slaves.append(address)

            self.slaves = cycle(slaves)
            self.slave_count = len(slaves)

        # If we're slave make sure we're kept track of for master
        else:
            try:
                session.execute(UPDATE_INSTANCES_QUERY, {'me': self.me})
                session.commit()
            except:
                logger.exception('Failed updating slave status')

            self.slave_count = 0
            self.slaves = cycle([])

        session.close()

    def update_forever(self):
        while True:
            old_status = self.is_master
            self.update_status()
            new_status = self.is_master

            if old_status != new_status:
                log = logger.info
            else:
                log = logger.debug

            if new_status:
                log('I am the sender master.')
            else:
                log('I am not the sender master.')

            metrics.set('slave_instance_count', self.slave_count)
            metrics.set('is_master_sender', int(self.is_master))

            # keep track of task to purge old slave instances if i'm master; kill
            # it otherwise
            if self.is_master:
                if not bool(self.prune_old_instances_task):
                    self.prune_old_instances_task = spawn(self.prune_old_instances)
            else:
                if bool(self.prune_old_instances_task):
                    self.prune_old_instances_task.kill()

            sleep(UPDATE_FREQUENCY)

    def prune_old_instances(self):
        while True:
            logger.info('Purging any old instances')

            try:
                session = db.Session()
                session.execute(REMOVE_OLD_INSTANCES_QUERY, {'old_instances_timeout': REMOVE_OLD_INSTANCES_TIMEOUT})
                session.commit()
                session.close()
            except Exception:
                logger.exception('Failed purging old instances')
            finally:
                if session:
                    session.close()

            sleep(REMOVE_OLD_INSTANCES_FREQUENCY)
