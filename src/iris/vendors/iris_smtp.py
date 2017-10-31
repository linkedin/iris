# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from iris.constants import EMAIL_SUPPORT, IM_SUPPORT
from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import quopri
import time
import markdown
import dns.resolver
import dns.exception
import logging

logger = logging.getLogger()


class iris_smtp(object):
    supports = frozenset([EMAIL_SUPPORT, IM_SUPPORT])

    def __init__(self, config):
        self.config = config
        self.modes = {
            EMAIL_SUPPORT: self.send_email,
            IM_SUPPORT: self.send_email,
        }
        self.mx_sorted = []
        self.smtp_handles = {}  # map mailserver -> connection handle

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

        conn = None
        used_mx = None

        for mx in self.mx_sorted:
            old_handle = self.smtp_handles.get(mx)

            # Use previously created connection
            if old_handle:
                conn = old_handle
                used_mx = mx
                break

            # Otherwise try making a new one and storing it
            else:
                logger.info('Opening new MX connection for %s', mx)
                try:
                    smtp = SMTP(timeout=self.smtp_timeout)
                    smtp.connect(mx[1], 25)
                    conn = smtp
                    self.smtp_handles[mx] = conn
                    used_mx = mx
                    break
                except Exception as e:
                    logger.exception('Failed connecting to %s: %s', mx, e)

        if not conn:
            raise Exception('Failed to get smtp connection.')

        try:
            conn.sendmail([from_address], [message['destination']], m.as_string())
        except Exception as e:
            logger.exception('Failed sending email through %s: %s', used_mx, e)

            # When we fail, remove this handle from our map so we try connecting again next round
            self.smtp_handles.pop(used_mx, None)

            try:
                conn.quit()
            except Exception:
                logger.exception('Failed closing SMTP connection')

            return None

        return time.time() - start

    def send(self, message):
        return self.modes[message['mode']](message)
