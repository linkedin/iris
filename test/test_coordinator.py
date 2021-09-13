from gevent import spawn, monkey, sleep, socket
monkey.patch_all()

import pytest  # noqa

zk_address = ('localhost', 2181)
zk_url = '%s:%s' % zk_address


class TestFailover():
    @classmethod
    def setup_class(cls):
        cls.instances = {}

    @classmethod
    def teardown_class(cls):
        for instance in cls.instances.values():
            instance.leave_cluster()

    def test_failover(self):
        from iris.coordinator.kazoo import Coordinator

        # If we can't connect to zk, skip
        try:
            sock = socket.socket()
            sock.connect(zk_address)
            sock.close()
        except socket.error:
            pytest.skip('Skipping this test as ZK server is not running/reachable.')

        # Create an initial instance which should become leader
        self.instances['c1'] = Coordinator(zk_url, 'testinstance', '1001', True)
        spawn(self.instances['c1'].update_forever)
        sleep(3)
        assert self.instances['c1'].am_i_leader()

        # Make another instance which should become follower
        self.instances['c2'] = Coordinator(zk_url, 'testinstance', '1002', True)
        spawn(self.instances['c2'].update_forever)
        sleep(3)
        assert self.instances['c2'].am_i_leader() is False

        # Verify it became follower
        sleep(3)
        assert self.instances['c1'].follower_count == 1
        assert next(self.instances['c1'].followers) == ('testinstance', 1002)

        # Verify API can see these instances
        self.instances['api'] = Coordinator(zk_url, None, None, False)
        assert self.instances['api'].get_current_leader() == ('testinstance', 1001)
        assert ('testinstance', 1002) in self.instances['api'].get_current_followers()

        # Kill off first leader and see if follower becomes leader with no followers
        self.instances['c1'].leave_cluster()
        sleep(5)
        assert self.instances['c2'].am_i_leader()
        assert self.instances['c2'].follower_count == 0

        # Start old leader again and see if it becomes a follower
        self.instances['c1'] = Coordinator(zk_url, 'testinstance', '1001', True)
        spawn(self.instances['c1'].update_forever)
        sleep(5)
        assert self.instances['c1'].am_i_leader() is False

        # It should show up as a follower to self.instances['c2'] which is now leader
        assert self.instances['c2'].am_i_leader()
        assert self.instances['c2'].follower_count == 1
        assert next(self.instances['c2'].followers) == ('testinstance', 1001)


def test_non_cluster():
    from iris.coordinator.noncluster import Coordinator

    assert Coordinator(False, []).am_i_leader() is False

    leader_without_followers = Coordinator(True, [])
    assert leader_without_followers.am_i_leader()
    assert leader_without_followers.follower_count == 0

    leader_with_followers = Coordinator(True, [{'host': 'testinstance', 'port': 1001}, {'host': 'testinstance', 'port': 1002}])
    assert leader_with_followers.am_i_leader()
    assert leader_with_followers.follower_count == 2

    followers = leader_with_followers.followers
    assert next(followers) == ('testinstance', 1001)
    assert next(followers) == ('testinstance', 1002)
    assert next(followers) == ('testinstance', 1001)
    assert next(followers) == ('testinstance', 1002)
