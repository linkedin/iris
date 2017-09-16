from iris.bin.owasync import is_pointless_message, relay, default_metrics
from exchangelib.items import Message
from exchangelib.properties import MessageHeader, Mailbox
from iris import metrics
from iris.client import IrisClient
import requests_mock


def test_is_pointless_message():
    bad_message_headers = [{
        'name': 'X-Autoreply',
        'value': 'yes'
    }]

    bad_message2_headers = [
        {
            'name': 'Auto-Submitted',
            'value': 'auto-replied'
        },
        {
            'name': 'Precedence',
            'value': 'bulk'
        }
    ]

    good_message_headers = [{
        'name': 'From',
        'value': 'Foo Bar <foo@bar.com>'
    }]

    assert is_pointless_message(bad_message_headers)
    assert is_pointless_message(bad_message2_headers)
    assert not is_pointless_message(good_message_headers)


def test_metrics():
    metrics.stats.update(default_metrics)
    bad_message = Message(headers=None, sender=Mailbox(email_address=''))
    relay(bad_message, None)
    assert metrics.stats['message_ignore_count'] == 1

    metrics.stats.update(default_metrics)
    bad_message = Message(headers=[MessageHeader(name='X-Autoreply', value='yes')], sender=Mailbox(email_address=''))
    relay(bad_message, None)
    assert metrics.stats['message_ignore_count'] == 1

    fake_iris_client = IrisClient('http://localhost')
    good_message = Message(headers=[], sender=Mailbox(email_address=''), text_body='')

    with requests_mock.mock() as m:
        m.post('http://localhost/v0/response/email')
        metrics.stats.update(default_metrics)
        relay(good_message, fake_iris_client)
        assert metrics.stats['message_relay_success_count'] == 1
        assert metrics.stats['incident_created_count'] == 0

    with requests_mock.mock() as m:
        m.post('http://localhost/v0/response/email', headers={'X-IRIS-INCIDENT': '1234'})
        metrics.stats.update(default_metrics)
        relay(good_message, fake_iris_client)
        assert metrics.stats['message_relay_success_count'] == 1
        assert metrics.stats['incident_created_count'] == 1

    with requests_mock.mock() as m:
        m.post('http://localhost/v0/response/email', status_code=500)
        metrics.stats.update(default_metrics)
        relay(good_message, fake_iris_client)
        assert metrics.stats['message_relay_failure_count'] == 1

    with requests_mock.mock() as m:
        m.post('http://localhost/v0/response/email', status_code=400)
        metrics.stats.update(default_metrics)
        relay(good_message, fake_iris_client)
        assert metrics.stats['malformed_message_count'] == 1
