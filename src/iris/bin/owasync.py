from gevent import monkey, sleep, spawn
monkey.patch_all()  # NOQA

from iris import metrics
from iris.config import load_config
from iris.sender.cache import IrisClient
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
    'owa_api_failure': 0,
    'message_relay_success': 0,
    'message_relay_failure': 0,
    'total_inbox_count': 0,
    'unread_inbox_count': 0
}


def poll(account, iris_client):

    try:
        metrics.set('total_inbox_count', account.inbox.total_count)
        metrics.set('unread_inbox_count', account.inbox.unread_count)
    except EWSError:
        logger.exception('Failed to gather inbox counts from OWA API')
        metrics.incr('owa_api_failure')

    try:
        for message in account.inbox.filter(is_read=False).order_by('-datetime_received'):
            if relay(message, iris_client):
                message.is_read = True
                try:
                    message.save()
                except EWSError:
                    logger.exception('Failed to update read status')
                    metrics.incr('owa_api_failure')
    except EWSError:
        logger.exception('Failed to iterate through inbox')
        metrics.incr('owa_api_failure')


def relay(message, iris_client):
    # Get headers into the format the iris expects from gmail
    headers = [{'name': header.name, 'value': header.value} for header in message.headers]

    # To and From headers are strangely missing
    if message.to_recipients:
        headers.append({'name': 'To', 'value': message.to_recipients[0].email_address})
    headers.append({'name': 'From', 'value': message.sender.email_address})

    data = {'headers': headers, 'body': message.text_body.strip()}

    try:
        # TODO: add POST method and HMAC functionality to irisclient
        iris_client.post('v0/response/email', json=data)
        metrics.incr('message_relay_success')
        return True
    except (requests.exceptions.RequestException):
        metrics.incr('message_relay_failure')
        logger.exception('Failed posting message %s (from %s) to iris-api', message.message_id, message.sender.email_address)
        return False


def main():
    config = load_config()

    metrics.init(config, 'iris-owa-sync', default_metrics)

    owaconfig = config.get('owa')

    if not owaconfig:
        logger.critical('Missing OWA configs')
        sys.exit(1)

    creds = Credentials(**owaconfig['credentials'])

    account = Account(
        primary_smtp_address=owaconfig['smtp_address'],
        credentials=creds,
        autodiscover=True,
        access_type=DELEGATE)
    logger.info('Receiving mail on behalf of %s', owaconfig['smtp_address'])

    nap_time = 60

    api_host = config.get('sender', {}).get('api_host', 'http://localhost:16649')
    iris_client = IrisClient(api_host)

    spawn(metrics.emit_forever)

    while True:
        start_time = time.time()
        poll(account, iris_client)
        run_time = time.time() - start_time
        logger.info('Last run took %2.f seconds. Waiting %s seconds until next poll..', run_time, nap_time)
        sleep(nap_time)
