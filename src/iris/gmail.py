# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

# coding: utf-8
# pylint: disable=star-args

from base64 import urlsafe_b64encode
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# from getpass import getuser
from logging import getLogger
from mimetypes import guess_type
from os import makedirs
from os.path import basename, exists, join

from googleapiclient import errors
from googleapiclient.discovery import build
from httplib2 import Http, ProxyInfo, socks
from oauth2client import client, tools
from oauth2client.file import Storage
# TODO: figure out why keyring fails on OS X
# from oauth2client.keyring_storage import Storage

logger = getLogger(__name__)


class Gmail(object):
    """
    :param config: gmail configuration
    """
    def __init__(self, config, proxy_cfg=None):
        self.config = config
        if proxy_cfg:
            proxy_info = ProxyInfo(
                socks.PROXY_TYPE_HTTP_NO_TUNNEL,
                proxy_cfg['host'],
                proxy_cfg['port']
            )
        else:
            proxy_info = None
        self.http = Http(proxy_info=proxy_info)
        self.client = None

    def _get_credentials(self):
        """Get OAuth credentials

        :return: OAuth credentials
        :rtype: :class:`oauth2client.client.Credentials`
        """
        credential_dir = join(self.config['creds_cache_dir'], 'cached_oauth_credentials')
        if not exists(credential_dir):
            makedirs(credential_dir)
        credential_path = join(credential_dir, 'googleapis.json')

        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.config['creds'],
                                                  self.config['scope'])
            flow.user_agent = 'Iris Gmail Integration'
            credentials = tools.run_flow(
                flow, store, tools.argparser.parse_args(args=['--noauth_local_webserver']))
            logger.info('Storing credentials to %s' % credential_path)
        else:
            credentials.refresh(self.http)
        return credentials

    def _get_http(self):
        """Construct httplib2.Http resource.

        :return: An object through which HTTP request will be made.
        :rtype: :class:`httplib2.Http`
        """
        return self._get_credentials().authorize(self.http)

    def connect(self):
        """Construct a Resource for interacting with the Gmail v1 API.

        :rtype: `None`
        """
        if self.client is None:
            self.client = build('gmail', 'v1', http=self._get_http())

    @staticmethod
    def create_message(
            sender,
            receiver,
            subject,
            payload):
        """Create a message for an email.

        :param sender: Email address of the sender.
        :param receiver: Email address of the receiver.
        :param subject: The subject of the email message.
        :param payload: The text of the email message.
        :return: An object containing a base64url encoded email object.
        :rtype: dict
        """
        message = MIMEText(payload)
        message['to'] = receiver
        message['from'] = sender
        message['subject'] = subject
        return {'raw': urlsafe_b64encode(message.as_string())}

    @staticmethod
    def create_message_with_attachment(
            sender,
            receiver,
            subject,
            message_text,
            path):
        """Create a message for an email.

        :param sender: Email address of the sender.
        :param receiver: Email address of the receiver.
        :param subject: The subject of the email message.
        :param message_text: The text of the email message.
        :param path: The name of the file to be attached.
        :return: An object containing a base64url encoded email object.
        :rtype: dict
        """
        message = MIMEMultipart()
        message['to'] = receiver
        message['from'] = sender
        message['subject'] = subject

        msg = MIMEText(message_text)
        message.attach(msg)

        content_type, encoding = guess_type(path)

        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'

        main_type, sub_type = content_type.split('/', 1)

        with open(path, 'r') as attachment:
            if main_type == 'text':
                msg = MIMEText(attachment.read(), _subtype=sub_type)
            elif main_type == 'image':
                msg = MIMEImage(attachment.read(), _subtype=sub_type)
            elif main_type == 'audio':
                msg = MIMEAudio(attachment.read(), _subtype=sub_type)
            else:
                msg = MIMEBase(main_type, sub_type)
                msg.set_payload(attachment.read())

        msg.add_header(
            'Content-Disposition',
            'attachment',
            filename=basename(path))
        message.attach(msg)

        return {'raw': urlsafe_b64encode(message.as_string())}

    def send_message(
            self,
            body='',
            user_id='me',
            **kwargs):
        """Send an email message.

        :param body: Message to be sent.
        :param user_id: User's email address. The special value "me" can be used
            to indicate the authenticated user.
        :return: Sent Message.
        :rtype: dict
        """
        self.connect()
        if not body:
            kwargs = dict(list({
                'sender': self.config.get('sub')
            }.items()) + list(kwargs.items()))
            body = self.create_message(**kwargs)
        ret = {}
        try:
            ret = (self.client.users().messages().send(
                userId=user_id,
                body=body
            ).execute())
        except errors.HttpError as error:
            logger.error('An error occurred: %s', error)
        else:
            logger.info('Message Id: %s', ret.get('id', ''))
        return ret

    @staticmethod
    def _fqrn(
            resource_type,
            project,
            resource):
        """Return a fully qualified resource name for Cloud Pub/Sub.

        :param resource_type:
        :param project:
        :param resource:
        :rtype: str
        """
        return "projects/{0}/{1}/{2}".format(project, resource_type, resource)

    def _get_full_topic_name(
            self,
            project,
            topic):
        """Return a fully qualified topic name.

        :param project:
        :param topic:
        :rtype: str
        """
        return self._fqrn('topics', project, topic)

    def watch(
            self,
            project,
            topic,
            user_id='me'):
        """Setup watching on user's Inbox

        :param project:
        :param topic:
        :param user_id: User's email address. The special value "me" can be used
            to indicate the authenticated user.
        :rtype: dict
        """
        self.connect()
        body = {
            'labelIds': ['INBOX', 'UNREAD'],
            'topicName': self._get_full_topic_name(project, topic)
        }
        ret = {}
        try:
            ret = self.client.users().watch(
                userId=user_id,
                body=body
            ).execute()
        except errors.HttpError as error:
            logger.error('An error occurred: %s', error)
        else:
            logger.debug('Watch expiration: %s', ret.get('expiration', ''))
        return ret
