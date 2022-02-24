import logging
import requests
import time
from iris.constants import PUSHOVER_SUPPORT

logger = logging.getLogger(__name__)


class iris_pushover(object):
    supports = frozenset([PUSHOVER_SUPPORT])

    def __init__(self, config):
        self.config = config
        self.modes = {
            'pushover': self.send_message
        }
        self.proxy = None
        if 'proxy' in self.config:
            host = self.config['proxy']['host']
            port = self.config['proxy']['port']
            self.proxy = {'http': '%s:%s' % (host, port),
                          'https': '%s:%s' % (host, port)}
        self.app_token = self.config.get('app_token')
        self.priority = int(self.config.get('priority'))
        self.sound = self.config.get('sound')
        self.debug = self.config.get('debug')
        self.api_url = self.config.get('api_url')
        self.timeout = config.get('timeout', 10)


    def send_message(self, message):
        start = time.time()

        data = {
            'token': self.app_token,
            'priority': self.priority,
            'sound': self.sound,
            'user': message['destination'],
            'message': message['body'],
            'title': message['context']['title']
        }

        if self.debug:
            logger.info('debug: %s', data)
        else:
            try:
                response = requests.post(self.api_url,
                                         data=data,
                                         proxies=self.proxy,
                                         timeout=self.timeout)
                if response.status_code == 200 or response.status_code == 204:
                    return time.time() - start
                else:
                    logger.error('Failed to send message to pushover: %d',
                                 response.status_code)
                    logger.error("Response: %s", response.content)
            except Exception as err:
                logger.exception('Pushover post request failed: %s', err)

    def send(self, message, customizations=None):
        return self.modes[message['mode']](message)
