# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from iris.constants import EMAIL_SUPPORT, IM_SUPPORT
from smtplib import SMTP, SMTPServerDisconnected
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import quopri
import time
import markdown
import dns.resolver
import dns.exception
import logging
import math
import itertools

logger = logging.getLogger(__name__)


class iris_smtp(object):
    supports = frozenset([EMAIL_SUPPORT, IM_SUPPORT])

    def __init__(self, config):
        self.config = config
        self.modes = {
            EMAIL_SUPPORT: self.send_email,
            IM_SUPPORT: self.send_email,
        }

        self.mx_lookup_expire = None
        self.mx_lookup_result = None

        self.smtp_connection_counts = None
        self.smtp_connection_cycle = None

        self.smtp_server = config.get('smtp_server')
        self.smtp_gateway = config.get('smtp_gateway')

        self.smtp_timeout = config.get('timeout', 10)
        self.connections_per_mx = config.get('connections_per_mx', 4)

        if not self.smtp_server and not self.smtp_gateway:
            raise ValueError('Missing SMTP config for sender')

    def get_mx_hosts(self):

        # If we have a stored mx result that isn't expired just give that back
        if self.mx_lookup_result is not None and (self.mx_lookup_expire == 0 or self.mx_lookup_expire > time.time()):
            return self.mx_lookup_result

        # If we just have one smtp server hard coded in config, mock it instead of doing a real
        # mx record lookup
        if self.smtp_server:
            self.mx_lookup_result = [(1, self.smtp_server)]
            self.mx_lookup_expire = 0
            return self.mx_lookup_result

        # Otherwise do MX record lookups on the given gateway
        elif self.smtp_gateway:
            try:
                mx_hosts = dns.resolver.query(self.smtp_gateway, 'MX')
            except:
                logger.exception('Failed looking up MX records for %s', self.smtp_gateway)
                return []
            else:
                self.mx_lookup_expire = mx_hosts.expiration
                self.mx_lookup_result = sorted((max(1, mx.preference), mx.exchange.to_text().strip('.')) for mx in mx_hosts)
                return self.mx_lookup_result

    def generate_pool_counts(self):
        mx_hosts = self.get_mx_hosts()
        if not mx_hosts:
            return {}

        first_priority = mx_hosts[0][0]

        counts = {}
        for priority, host in mx_hosts:
            host_percentage = first_priority / float(priority)
            connection_count = int(math.ceil(host_percentage * self.connections_per_mx))
            counts[host] = connection_count

        return counts

    def maintain_connection_pools(self):

        num_previous_connections = None

        if self.smtp_connection_counts is None:
            self.smtp_connection_counts = self.generate_pool_counts()
        else:
            # MX records haven't expired? Don't regenerate pools and bail
            if self.mx_lookup_result is not None and (self.mx_lookup_expire == 0 or self.mx_lookup_expire > time.time()):
                return True

            new_connection_counts = self.generate_pool_counts()

            # If the MX records expired but the values are the same, bail
            if new_connection_counts == self.smtp_connection_counts:
                return True

            num_previous_connections = sum(self.smtp_connection_counts.itervalues())
            self.smtp_connection_counts = new_connection_counts

        connections = []

        for host, count in self.smtp_connection_counts.iteritems():
            logger.info('Opening %d SMTP connections to %s', count, host)
            for x in xrange(count):
                try:
                    connections.append([host, self.open_smtp_connection(host)])
                except Exception:
                    logger.exception('Failed opening smtp connection %d/%d to %s', x + 1, count, host)

        if not connections:
            return False

        # Atomically set new cycle list and get access to old one
        old_cycle, self.smtp_connection_cycle = self.smtp_connection_cycle, itertools.cycle(connections)

        # Try to kill all old connections in our old cycle object
        if num_previous_connections is not None and old_cycle is not None:
            for x in xrange(num_previous_connections):
                try:
                    old_connection = old_cycle.next()
                except StopIteration:
                    break

                try:
                    old_connection[1].quit()
                except:
                    pass

        return True

    def open_smtp_connection(self, address):
        smtp = SMTP(timeout=self.smtp_timeout)
        smtp.connect(address, 25)
        return smtp

    def send_email(self, message):
        md = markdown.Markdown()
        from_address = self.config['from']

        start = time.time()
        m = MIMEMultipart('alternative')
        m['from'] = from_address
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

        # Maintain our connection pools. This will fail if we either have 0 MX records
        # or fail to actually open connections to any of the MX records themselves
        if not self.maintain_connection_pools():
            logger.error('Failed creating any connection pools!')
            return None

        # Get a connection object from the cycle. Will be a list like [MX Name, MX Handle],
        # so if we reconnect we can just update the handle in place
        try:
            connection = self.smtp_connection_cycle.next()
        except StopIteration:
            logger.error('Empty cycle for smtp connections!')
            return None

        try:
            connection[1].sendmail([from_address], [message['destination']], m.as_string())

        # If it's a disconnect, probably caused by timeout, try reconnecting and trying again
        except SMTPServerDisconnected:
            logger.exception('SMTP server disconnected while trying to send message %s through server %s. Will try to reconnect + send.', message, connection[0])

            # Try cleaning up
            try:
                connection[1].quit()
            except:
                pass

            # Try restoring this connection object
            try:
                connection[1] = self.open_smtp_connection(connection[0])
            except Exception:
                logger.exception('Failed reconnecting to SMTP host %s', connection[0])
                return None

            try:
                connection[1].sendmail([from_address], [message['destination']], m.as_string())
                logger.info('Message successfully sent through %s after reconnecting', connection[0])
            except Exception:
                logger.exception('Failed sending message again')
                return None

        # Anything else just try reconnecting and let this call fail, as it will be retried
        except Exception:
            logger.exception('Failed sending message %s through server %s. Will try to reconnect.', message, connection[0])

            # Try cleaning up
            try:
                connection[1].quit()
            except:
                pass

            # Try restoring this connection object
            try:
                connection[1] = self.open_smtp_connection(connection[0])
            except Exception:
                logger.exception('Failed reconnecting to SMTP host %s', connection[0])

            # Mark this send as a failure. The message will be retried later.
            return None

        return time.time() - start

    def send(self, message):
        return self.modes[message['mode']](message)
