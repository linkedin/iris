# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from gevent import sleep
from iris.constants import EMAIL_SUPPORT, IM_SUPPORT
from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from iris import cache
import quopri
import time
import markdown
import dns.resolver
import dns.exception
import logging

logger = logging.getLogger(__name__)


class iris_smtp(object):
    supports = frozenset([EMAIL_SUPPORT, IM_SUPPORT])

    last_autoscale_mx_lookup = {}

    def __init__(self, config):
        self.config = config
        self.retry_interval = config.get('retry_interval', 0)
        self.modes = {
            EMAIL_SUPPORT: self.send_email,
            IM_SUPPORT: self.send_email,
        }
        self.mx_sorted = []
        self.last_conn = None
        self.last_conn_server = None

        self.smtp_timeout = config.get('timeout', 10)
        if config.get('smtp_server'):
            # mock mx record
            self.mx_sorted.append((0, config['smtp_server']))
        elif config.get('smtp_gateway'):
            try:
                mx_hosts = dns.resolver.query(config['smtp_gateway'], 'MX')
            except dns.exception.DNSException as e:
                mx_hosts = []
                raise Exception('MX error: %s' % e)
            for mx in mx_hosts:
                mx_hostname = mx.exchange.to_text().strip('.')
                self.mx_sorted.append((mx.preference, mx_hostname))
            self.mx_sorted.sort(key=lambda tup: tup[0])
        else:
            raise ValueError('Missing SMTP config for sender')

    def send_email(self, message, customizations=None):
        md = markdown.Markdown()

        start = time.time()
        m = MIMEMultipart('alternative')

        from_address = self.config['from']
        application = message.get('application')
        if application:
            m['X-IRIS-APPLICATION'] = application
            address = cache.applications.get(application, {}).get('custom_sender_addresses', {}).get('email')
            if address is not None:
                from_address = address

        priority = message.get('priority')
        if priority:
            m['X-IRIS-PRIORITY'] = priority

        plan = message.get('plan')
        if plan:
            m['X-IRIS-PLAN'] = plan

        incident_id = message.get('incident_id')
        if incident_id:
            m['X-IRIS-INCIDENT-ID'] = str(incident_id)

        m['Date'] = formatdate(localtime=True)
        m['from'] = from_address
        if message.get('multi-recipient'):
            m['to'] = ','.join(set(message['destination']))
            if message['bcc_destination']:
                m['bcc'] = ','.join(set(message['bcc_destination']))
        else:
            m['to'] = message['destination']
        if message.get('noreply'):
            m['reply-to'] = m['to']

        if 'email_subject' in message:
            m['subject'] = message['email_subject']
        else:
            m['subject'] = message['subject']

        plaintext = None

        if 'email_text' in message:
            plaintext = message['email_text']
        elif 'body' in message:
            plaintext = message['body']

        if plaintext:
            mt = MIMEText(None, 'plain', 'utf-8')
            mt.set_payload(quopri.encodestring(plaintext.encode('UTF-8')))
            mt.replace_header('Content-Transfer-Encoding', 'quoted-printable')
            m.attach(mt)

        # for tracking messages, email_html is not required, so it's possible
        # that both of the following keys are missing from message
        html = None

        if 'email_html' in message:
            html = message['email_html']
        elif 'body' in message:
            html = md.convert(message['body'])

        if html:
            if 'extra_html' in message:
                html += message['extra_html']
            # We need to have body tags for the oneclick buttons to properly parse
            html = '<body>\n' + html + '\n</body>'
            mt = MIMEText(None, 'html', 'utf-8')
            # Google does not like base64 encoded emails for the oneclick button functionalty,
            # so force quoted printable.
            mt.set_payload(quopri.encodestring(html.encode('UTF-8')))
            mt.replace_header('Content-Transfer-Encoding', 'quoted-printable')
            m.attach(mt)

        conn = None

        if message.get('multi-recipient'):
            email_recipients = message['destination'] + message['bcc_destination']
        else:
            email_recipients = [message['destination']]
        # Try reusing previous connection in this worker if we have one
        if self.last_conn:
            conn = self.last_conn
        else:
            for mx in self.mx_sorted:
                try:
                    smtp = SMTP(timeout=self.smtp_timeout)
                    smtp.connect(mx[1], self.config.get('port', 25))
                    if self.config.get('username', None) is not None and self.config.get('password', None) is not None:
                        smtp.login(self.config.get('username', None), self.config.get('password', None))
                    conn = smtp
                    self.last_conn = conn
                    self.last_conn_server = mx[1]
                    break
                except Exception as e:
                    logger.exception(e)

        if not conn:
            raise Exception('Failed to get smtp connection.')

        try:
            conn.sendmail([from_address], email_recipients, m.as_string())
        except Exception:
            logger.warning('Failed sending email through %s. Will try connecting again and resending.', self.last_conn_server)

            try:
                conn.quit()
            except Exception:
                pass

            # If we can't send it, try reconnecting and then sending it one more time before
            # giving up
            for mx in self.mx_sorted:
                try:
                    smtp = SMTP(timeout=self.smtp_timeout)
                    smtp.connect(mx[1], 25)
                    conn = smtp
                    self.last_conn = conn
                    self.last_conn_server = mx[1]
                    break
                except Exception as e:
                    logger.exception('Failed reconnecting to %s to send message', self.last_conn_server)
                    self.last_conn = None
                    return None

            try:
                # If configured, sleep to back-off on connection
                if self.retry_interval:
                    sleep(self.retry_interval)
                conn.sendmail([from_address], email_recipients, m.as_string())
                logger.info('Message successfully sent through %s after reconnecting', self.last_conn_server)
            except Exception:
                logger.exception('Failed sending email through %s after trying to reconnect', self.last_conn_server)
                return None

        return time.time() - start

    def send(self, message, customizations=None):
        return self.modes[message['mode']](message, customizations)

    def cleanup(self):
        if self.last_conn:
            logger.info('Trying to quit smtp connection to %s', self.last_conn_server)
            try:
                self.last_conn.quit()
            except Exception:
                pass

    @classmethod
    def determine_worker_count(cls, vendor):
        mx_gateway = vendor.get('smtp_gateway')
        connections_per_mx = int(vendor.get('tasks_per_mx', 4))

        last_lookup = cls.last_autoscale_mx_lookup.get(mx_gateway)
        now = time.time()

        if last_lookup and last_lookup[0] > now:
            logger.info('Using old MX results for %s; next MX refresh in %d seconds', mx_gateway, last_lookup[0] - now)
            return last_lookup[1]
        else:
            logger.info('Refreshing MX records for %s', mx_gateway)

            try:
                mx_result = dns.resolver.query(mx_gateway, 'MX')
                mx_hosts = [mx.exchange.to_text().strip('.') for mx in mx_result]
            except dns.exception.DNSException as e:
                mx_hosts = []

                if last_lookup:
                    logger.error('Failed looking up MX: %s; returning old results.', e)
                    return last_lookup[1]
                else:
                    raise Exception('MX error, and we don\'t have old results to fall back on: %s' % e)

            mx_host_counts = {mx: connections_per_mx for mx in mx_hosts}
            cls.last_autoscale_mx_lookup[mx_gateway] = (mx_result.expiration, mx_host_counts)
            logger.info('Next MX refresh for %s in %d seconds', mx_gateway, mx_result.expiration - now)
            return mx_host_counts
