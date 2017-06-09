from gevent import monkey, sleep, spawn
monkey.patch_all()  # NOQA

from iris import metrics
from iris.config import load_config
from iris.client import IrisClient
from exchangelib import DELEGATE, Account, Credentials
from exchangelib.errors import EWSError
import sys
import logging
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

default_metrics = {
    'owa_api_failure_count': 0,
    'message_relay_success_count': 0,
    'message_relay_failure_count': 0,
    'total_inbox_count': 0,
    'unread_inbox_count': 0,
    'message_process_count': 0,
    'message_ignore_count': 0,
}


email_headers_to_ignore = frozenset([('X-Autoreply', 'yes'),
                                     ('Auto-Submitted', 'auto-replied'),
                                     ('Precedence', 'bulk')])


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
    except EWSError:
        logger.exception('Failed to gather inbox counts from OWA API')
        metrics.incr('owa_api_failure_count')

    processed_messages = 0
    messages_to_mark_read = []

    try:
        for message in account.inbox.filter(is_read=False).order_by('-datetime_received'):
            processed_messages += 1

            relay(message, iris_client)

            # Mark it as read in bulk later. (This syntax isn't documented)
            message.is_read = True
            messages_to_mark_read.append((message, ('is_read', )))

    except EWSError:
        logger.exception('Failed to iterate through inbox')
        metrics.incr('owa_api_failure_count')

    if messages_to_mark_read:
        bulk_update_count = len(messages_to_mark_read)
        logger.info('will mark %s messages as read', bulk_update_count)
        try:
            account.bulk_update(items=messages_to_mark_read)
        except EWSError:
            logger.exception('Failed to update read status on %s messages in bulk', bulk_update_count)
            metrics.incr('owa_api_failure_count')

    metrics.set('message_process_count', processed_messages)
    return processed_messages


def relay(message, iris_client):
    # Get headers into the format the iris expects from gmail
    headers = [{'name': header.name, 'value': header.value} for header in message.headers]

    # If this is a bulk message or an auto reply or something else, don't bother sending it to iris-api
    if is_pointless_message(headers):
        logger.info('Not relaying pointless message %s (from %s) to iris-api', message.message_id, message.sender.email_address)
        metrics.incr('message_ignore_count')
        return

    # To and From headers are strangely missing
    if message.to_recipients:
        headers.append({'name': 'To', 'value': message.to_recipients[0].email_address})
    headers.append({'name': 'From', 'value': message.sender.email_address})

    data = {'headers': headers, 'body': message.text_body.strip()}

    try:
        iris_client.post('response/email', json=data).raise_for_status()
        metrics.incr('message_relay_success_count')
    except requests.exceptions.RequestException:
        metrics.incr('message_relay_failure_count')
        logger.exception('Failed posting message %s (from %s) to iris-api', message.message_id, message.sender.email_address)


def main():
    config = load_config()

    metrics.init(config, 'iris-owa-sync', default_metrics)

    owaconfig = config.get('owa')

    if not owaconfig:
        logger.critical('Missing OWA configs')
        sys.exit(1)

    api_host = owaconfig.get('api_host', 'http://localhost:16649')
    iris_client = IrisClient(api_host, 0, owaconfig['iris_app'], owaconfig['iris_app_key'])

    spawn(metrics.emit_forever)

    creds = Credentials(**owaconfig['credentials'])

    account = Account(
        primary_smtp_address=owaconfig['smtp_address'],
        credentials=creds,
        autodiscover=True,
        access_type=DELEGATE)
    logger.info('Receiving mail on behalf of %s', owaconfig['smtp_address'])

    try:
        nap_time = int(owaconfig.get('sleep_interval', 60))
    except ValueError:
        nap_time = 60

    while True:
        start_time = time.time()
        message_count = poll(account, iris_client)
        run_time = time.time() - start_time
        logger.info('Last run took %2.f seconds and processed %s messages. Waiting %s seconds until next poll..', run_time, message_count, nap_time)
        sleep(nap_time)
