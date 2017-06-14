import logging
from iris import db, metrics
from gevent import sleep
from itertools import cycle

logger = logging.getLogger(__name__)

UPDATE_FREQUENCY = 3
SENDER_ALIVE_TIMEOUT = 10

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


class Coordinator(object):
    def __init__(self, hostname, port):
        self.me = '%s:%s' % (hostname, port)
        self.is_master = None
        self.master = None

    def am_i_master(self):
        return self.is_master

    def get_current_master(self):
        session = db.Session()
        master = session.execute(GET_MASTER_QUERY).scalar()
        session.close()
        return self.address_to_tuple(master)

    def address_to_tuple(self, address):
        try:
            host, port = address.split(':', 1)
            return host, int(port)
        except (IndexError, ValueError):
            logger.error('Failed getting address tuple from %s', address)
            return None

    def update_status(self):
        session = db.Session()

        # Try setting us to the master otherwise do nothing
        session.execute(UPDATE_MASTER_QUERY, {'me': self.me, 'timeout': SENDER_ALIVE_TIMEOUT})
        session.commit()

        # Also keep track of us in the list of online senders
        session.execute(UPDATE_INSTANCES_QUERY, {'me': self.me})
        session.commit()

        # Keep track of the actual master locally
        self.master = session.execute(GET_MASTER_QUERY).scalar()

        # Record locally whether we're the master or not
        self.is_master = self.master == self.me

        # Keep track of the list of slaves (senders online that are not the master) locally
        slaves = []
        for row in session.execute(GET_SLAVES_QUERY, {'timeout': SENDER_ALIVE_TIMEOUT}):
            address = self.address_to_tuple(row[0])
            if address:
                slaves.append(address)

        self.slaves = cycle(slaves)
        self.slave_count = len(slaves)

        session.close()

    def update_forever(self):
        while True:
            old_status = self.is_master
            self.update_status()
            new_status = self.is_master

            if old_status != new_status:
                if new_status:
                    logger.info('I am now the sender master!')
                else:
                    logger.info('I am not the sender master. The current master is %s', self.master)
            else:
                logger.debug('I %s the master sender.', 'AM' if self.is_master else 'AM NOT')

            logger.debug('I am aware of %s slaves in this cluster', self.slave_count)

            # Only one node in the cluster should ever emit this as 1
            metrics.set('is_master_sender', int(self.is_master))

            # Every node in the cluster will end up being aware of the slaves
            metrics.set('slave_instance_count', self.slave_count)

            sleep(UPDATE_FREQUENCY)
