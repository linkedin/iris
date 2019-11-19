from gevent import monkey, sleep
monkey.patch_all()  # NOQA

from iris import metrics
from iris.config import load_config
from iris.client import IrisClient
import exchangelib
import exchangelib.errors
import exchangelib.protocol
import sys
import logging
import logging.handlers
import os
import time
import requests


logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
log_file = os.environ.get('OWA_SYNC_LOG_FILE')
if log_file:
    ch = logging.handlers.RotatingFileHandler(log_file, mode='a', maxBytes=10485760, backupCount=10)
else:
    ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(ch)

pidfile = os.environ.get('OWA_SYNC_PIDFILE')
if pidfile:
    try:
        pid = os.getpid()
        with open(pidfile, 'w') as h:
            h.write('%s\n' % pid)
            logger.info('Wrote pid %s to %s', pid, pidfile)
    except IOError:
        logger.exception('Failed writing pid to %s', pidfile)

default_metrics = {
    'owa_api_failure_count': 0,  # we fail to hit EWS api. requests timeout or similar
    'message_relay_success_count': 0,  # iris-api gives 2xx
    'message_relay_failure_count': 0,  # iris-api gives 5xx
    'malformed_message_count': 0,  # iris-api gives 4xx (likely not fault, so don't blame ourselves)
    'total_inbox_count': 0,
    'unread_inbox_count': 0,
    'message_process_count': 0,
    'message_ignore_count': 0,
    'incident_created_count': 0,
}


email_headers_to_ignore = frozenset([('X-Autoreply', 'yes'),
                                     ('Auto-Submitted', 'auto-replied'),
                                     ('Precedence', 'bulk')])


# per exchangelib docs, to customize the http requests sent (eg to add a proxy)
# need to create a custom requests adapter
class UseProxyHttpAdapter(requests.adapters.HTTPAdapter):
    _my_proxies = None

    def send(self, *args, **kwargs):
        if self._my_proxies:
            kwargs['proxies'] = self._my_proxies
        return super(UseProxyHttpAdapter, self).send(*args, **kwargs)


def split_in_batches(l, n):
    # For item i in a range that is a length of l,
    for i in range(0, len(l), n):
        # Create an index range for l of n items:
        yield l[i:i + n]


def is_pointless_message(headers):
    for header in email_headers_to_ignore:
        if {'name': header[0], 'value': header[1]} in headers:
            logger.warning('Filtering out message due to header combination %s: %s', *header)
            return True
    return False


def poll(account, iris_client):

    try:
        metrics.set('total_inbox_count', account.inbox.total_count)
        metrics.set('unread_inbox_count', account.inbox.unread_count)
    except (exchangelib.errors.EWSError, requests.exceptions.RequestException):
        logger.exception('Failed to gather inbox counts from OWA API')
        metrics.incr('owa_api_failure_count')

    processed_messages = 0
    messages_to_mark_read = []
    messages_to_delete = []

    try:
        for message in account.inbox.filter(is_read=False).order_by('-datetime_received'):
            processed_messages += 1

            try:
                result = relay(message, iris_client)
                if not result:
                    messages_to_delete.append(message)
            except Exception:
                logger.exception('Uncaught exception during message relaying')
                metrics.incr('message_relay_failure_count')

            # Mark it as read in bulk later. (This syntax isn't documented)
            message.is_read = True
            messages_to_mark_read.append((message, ('is_read', )))

    except (exchangelib.errors.EWSError, requests.exceptions.RequestException):
        logger.exception('Failed to iterate through inbox')
        metrics.incr('owa_api_failure_count')

    if messages_to_mark_read:
        # mark as read in batches of 100 messages
        messages_in_batches = split_in_batches(messages_to_mark_read, 100)
        for batch in messages_in_batches:
            bulk_update_count = len(batch)
            logger.info('will mark %s messages as read', bulk_update_count)
            try:
                account.bulk_update(items=batch)
            except (exchangelib.errors.EWSError, requests.exceptions.RequestException):
                logger.exception('Failed to update read status on %s messages in bulk', bulk_update_count)
                metrics.incr('owa_api_failure_count')

    if messages_to_delete:
        for batch in split_in_batches(messages_to_delete, 100):
            bulk_delete_count = len(batch)
            logger.info('will delete %s messages', bulk_delete_count)
            try:
                account.bulk_delete(ids=batch)
            except (exchangelib.errors.EWSError, requests.exceptions.RequestException):
                logger.exception('Failed to delete on %s messages in bulk', bulk_delete_count)
                metrics.incr('owa_api_failure_count')

    metrics.set('message_process_count', processed_messages)
    return processed_messages


def relay(message, iris_client):
    if message.headers is None:
        logger.info('Ignoring message with no headers %s (from %s)', message.message_id, message.sender.email_address)
        metrics.incr('message_ignore_count')
        return True

    # Get headers into the format the iris expects from gmail
    headers = [{'name': header.name, 'value': header.value} for header in message.headers]

    # If this is a bulk message or an auto reply or something else, don't bother sending it to iris-api
    if is_pointless_message(headers):
        logger.info('Not relaying pointless message %s (from %s) to iris-api', message.message_id, message.sender.email_address)
        metrics.incr('message_ignore_count')
        return True

    # To and From headers are strangely missing
    if message.to_recipients:
        headers.append({'name': 'To', 'value': [r.email_address for r in message.to_recipients]})
    headers.append({'name': 'From', 'value': message.sender.email_address})

    data = {'headers': headers, 'body': message.text_body.strip()}

    try:
        req = iris_client.post('response/email', json=data)
    except requests.exceptions.RequestException:
        metrics.incr('message_relay_failure_count')
        logger.exception('Failed posting message %s (from %s) to iris-api', message.message_id, message.sender.email_address)
        return False

    result = False
    code_type = req.status_code // 100

    if code_type == 5:
        metrics.incr('message_relay_failure_count')
        logger.error('Failed posting message %s (from %s) to iris-api. Got status code %s and response %s',
                     message.message_id, message.sender.email_address, req.status_code, req.text)

    elif code_type == 4:
        metrics.incr('malformed_message_count')
        logger.error('Failed posting message %s (from %s) to iris-api. Message likely malformed. Status code: %s. Response: %s',
                     message.message_id, message.sender.email_address, req.status_code, req.text)

    elif code_type == 2:
        metrics.incr('message_relay_success_count')

        # If we create an incident using an email, this header will be set and will be the numeric ID
        # of the created incident; otherwise, the header will not exist or it will be a textual
        # error message.
        incident_header = req.headers.get('X-IRIS-INCIDENT')
        if isinstance(incident_header, str) and incident_header.isdigit():
            metrics.incr('incident_created_count')
            result = True

    else:
        logger.error('Failed posting message %s (from %s) to iris-api. Message likely malformed. Got back strange status code: %s. Response: %s',
                     message.message_id, message.sender.email_address, req.status_code, req.text)

    return result


def main():
    boot_time = time.time()
    config = load_config()

    metrics.init(config, 'iris-owa-sync', default_metrics)

    owaconfig = config.get('owa')

    if not owaconfig:
        logger.critical('Missing OWA configs')
        sys.exit(1)

    api_host = owaconfig.get('api_host', 'http://localhost:16649')
    iris_client = IrisClient(api_host, 0, owaconfig['iris_app'], owaconfig['iris_app_key'])

    proxies = owaconfig.get('proxies')

    # only way to configure a proxy is to monkey-patch (http adapter) a monkey-patch (baseprotocol) :/
    if proxies:
        UseProxyHttpAdapter._my_proxies = proxies
        exchangelib.protocol.BaseProtocol.HTTP_ADAPTER_CLS = UseProxyHttpAdapter

    creds = exchangelib.ServiceAccount(**owaconfig['credentials'])

    try:
        nap_time = int(owaconfig.get('sleep_interval', 60))
    except ValueError:
        nap_time = 60

    while True:
        start_time = time.time()
        message_count = 0

        try:
            config = exchangelib.Configuration(credentials=creds, **owaconfig['config'])
            account = exchangelib.Account(
                config=config,
                access_type=exchangelib.DELEGATE,
                **owaconfig['account'])
        except (exchangelib.errors.EWSError, requests.exceptions.RequestException):
            logger.exception('Failed authenticating to OWA365')
            metrics.incr('owa_api_failure_count')
        else:
            logger.info('Receiving mail on behalf of %s', owaconfig['account'].get('primary_smtp_address'))
            message_count = poll(account, iris_client)

        now = time.time()
        run_time = now - start_time
        logger.info('Last run took %2.f seconds and processed %s messages. Waiting %s seconds until next poll..', run_time, message_count, nap_time)
        metrics.set('uptime', now - boot_time)
        metrics.emit()
        sleep(nap_time)
