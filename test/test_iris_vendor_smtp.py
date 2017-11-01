#!/usr/bin/env python
# -*- coding:utf-8 -*-

from collections import OrderedDict


def test_smtp_vendor_init():
    from iris.vendors.iris_smtp import iris_smtp
    smtp_config = {
        'smtp_server': 'foo'
    }
    smtp_vendor = iris_smtp(smtp_config)
    assert smtp_vendor.get_mx_hosts() == [(1, 'foo')]

    assert smtp_vendor.smtp_timeout == 10
    assert smtp_vendor.mx_lookup_result == [(1, 'foo')]

    smtp_config = {
        'timeout': 20,
        'smtp_server': 'foo'
    }
    smtp_vendor = iris_smtp(smtp_config)
    assert smtp_vendor.smtp_timeout == 20


def test_smtp_send_email(mocker):
    from iris.vendors.iris_smtp import iris_smtp
    smtp_config = {
        'smtp_server': 'foo',
        'connections_per_mx': 1,
        'from': 'iris@bar',
    }
    smtp_vendor = iris_smtp(smtp_config)
    mocked_SMPT = mocker.patch('iris.vendors.iris_smtp.SMTP')
    smtp_vendor.send_email({
        'destination': 'foo@bar',
        'subject': 'hello',
        'body': 'world',
    })
    mocked_SMPT.assert_called_once_with(timeout=10)

    class CheckEmailString(str):
        def __eq__(self, other):
            return 'hello' in other and 'world' in other

    mocked_SMPT.return_value.sendmail.assert_called_once_with(
        ['iris@bar'],
        ['foo@bar'],
        CheckEmailString())

    mocked_SMPT.reset_mock()

    smtp_vendor.send_email({
        'destination': 'foo@bar',
        'subject': 'hello',
        'body': 'world',
    })

    mocked_SMPT.assert_not_called()


def test_smtp_generate_pool_counts(mocker):
    # A single hard coded server should get 4 connections
    from iris.vendors.iris_smtp import iris_smtp
    smtp_config = {
        'smtp_server': 'fooserver',
        'connections_per_mx': 4,
        'from': 'iris@bar',
    }
    smtp_vendor = iris_smtp(smtp_config)
    assert smtp_vendor.generate_pool_counts() == {'fooserver': 4}

    # Two servers with same priority from DNS should get same number of connections,
    # which is configured to be 4
    smtp_config = {
        'smtp_gateway': 'foogateway',
        'connections_per_mx': 4,
        'from': 'iris@bar',
    }
    smtp_vendor = iris_smtp(smtp_config)
    smtp_vendor.get_mx_hosts = lambda: [(10, 'fooserver1'), (10, 'fooserver2')]
    assert smtp_vendor.generate_pool_counts() == {'fooserver1': 4, 'fooserver2': 4}

    # Two servers with differing priority from DNS will get a different number of connections
    smtp_config = {
        'smtp_gateway': 'foogateway',
        'connections_per_mx': 4,
        'from': 'iris@bar',
    }
    smtp_vendor = iris_smtp(smtp_config)
    smtp_vendor.get_mx_hosts = lambda: [(5, 'fooserver1'), (10, 'fooserver2')]
    assert smtp_vendor.generate_pool_counts() == {'fooserver1': 4, 'fooserver2': 2}

    # A bunch of servers will follow the same logic
    smtp_config = {
        'smtp_gateway': 'foogateway',
        'connections_per_mx': 4,
        'from': 'iris@bar',
    }
    smtp_vendor = iris_smtp(smtp_config)
    smtp_vendor.get_mx_hosts = lambda: [(10, 'lowserver1'), (10, 'lowserver2'), (20, 'highserver1')]
    assert smtp_vendor.generate_pool_counts() == {'lowserver1': 4, 'lowserver2': 4, 'highserver1': 2}


def test_maintain_connection_pools(mocker):
    from iris.vendors.iris_smtp import iris_smtp
    smtp_config = {
        'smtp_server': 'fooserver',
        'from': 'iris@bar',
    }

    # Simple case where given a single server with 10 connections, we should have called
    # the open function 10 times and have 10 of this in the cycle
    smtp_vendor = iris_smtp(smtp_config)
    smtp_vendor.open_smtp_connection = mocker.Mock()
    smtp_vendor.generate_pool_counts = lambda: {'fooserver': 10}
    smtp_vendor.maintain_connection_pools()

    smtp_vendor.open_smtp_connection.assert_called()
    smtp_vendor.open_smtp_connection.assert_called_with('fooserver')
    assert smtp_vendor.open_smtp_connection.call_count == 10
    for x in xrange(10):
        assert smtp_vendor.smtp_connection_cycle.next()[0] == 'fooserver'

    # More complex case where we should have multiple connections of different servers
    smtp_vendor = iris_smtp(smtp_config)
    smtp_vendor.open_smtp_connection = mocker.Mock()
    smtp_vendor.generate_pool_counts = lambda: OrderedDict((('fooserver', 10), ('twoserver', 2), ('anotherserver', 5)))
    smtp_vendor.maintain_connection_pools()

    smtp_vendor.open_smtp_connection.assert_called()
    assert smtp_vendor.open_smtp_connection.call_count == 17

    def test_cycle():
        for x in xrange(10):
            assert smtp_vendor.smtp_connection_cycle.next()[0] == 'fooserver'

        for x in xrange(2):
            assert smtp_vendor.smtp_connection_cycle.next()[0] == 'twoserver'

        for x in xrange(5):
            assert smtp_vendor.smtp_connection_cycle.next()[0] == 'anotherserver'

    # And around and around we go
    test_cycle()
    test_cycle()
    test_cycle()

    # Change the pool count and see if we recover and close old connections
    smtp_vendor.open_smtp_connection.reset_mock()

    # Make us reload the correct list of locations
    smtp_vendor.mx_lookup_result = None
    smtp_vendor.mx_lookup_expire = 0

    # Change the list of corrections
    smtp_vendor.generate_pool_counts = lambda: {'newserver': 10}

    # Grab the old cycle before its lost
    old_cycle = smtp_vendor.smtp_connection_cycle

    # This should create a new cycle and then close all of the old connections
    smtp_vendor.maintain_connection_pools()

    for x in xrange(10):
        old_connection = old_cycle.next()
        assert old_connection[0] == 'fooserver'
        assert old_connection[1].quit.called

    for x in xrange(2):
        old_connection = old_cycle.next()
        assert old_connection[0] == 'twoserver'
        assert old_connection[1].quit.called

    for x in xrange(5):
        old_connection = old_cycle.next()
        assert old_connection[0] == 'anotherserver'
        assert old_connection[1].quit.called

    # Should have created 10 new instances of newserver
    smtp_vendor.open_smtp_connection.assert_called()
    assert smtp_vendor.open_smtp_connection.call_count == 10

    for x in xrange(10):
        assert smtp_vendor.smtp_connection_cycle.next()[0] == 'newserver'


def test_smtp_unicode(mocker):
    from iris.vendors.iris_smtp import iris_smtp
    smtp_config = {
        'smtp_server': 'foo',
        'from': 'iris@bar',
    }
    smtp_vendor = iris_smtp(smtp_config)
    mocker.patch('iris.vendors.iris_smtp.SMTP')
    smtp_vendor.send_email({
        'destination': 'foo@bar',
        'subject': 'hello',
        'body': u'\u201c',
    })
