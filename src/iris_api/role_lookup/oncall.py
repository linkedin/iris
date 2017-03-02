# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import requests
from requests.exceptions import RequestException
import logging
from iris_api.metrics import stats

logger = logging.getLogger(__name__)


class oncall(object):
    def __init__(self, config):
        headers = requests.utils.default_headers()
        headers['User-Agent'] = 'iris-api role lookup (%s)' % headers.get('User-Agent')
        self.requests = requests.session()
        self.requests.headers = headers
        self.requests.verify = False
        self.endpoint = config['oncall-api'] + '/api/v0'

    def call_oncall(self, url):
        url = str(self.endpoint + url)
        try:
            r = self.requests.get(url)
        except RequestException:
            logger.exception('Failed hitting oncall-api for url "%s"', url)
            return None

        if r.status_code != 200:
            logger.error('Invalid response from oncall-api for URL "%s". Code: %s. Content: "%s"', url, r.status_code, r.content)
            return None

        try:
            return r.json()
        except ValueError:
            logger.exception('Failed decoding json from oncall-api. URL: "%s" Code: %s', url, r.status_code)
            return None

    def get(self, role, target):
        if role == 'team':
            result = self.call_oncall('/teams/%s/users' % target)
            if not isinstance(result, list):
                stats['oncall_error'] += 1
                return None
            return result
        elif role == 'manager':
            result = self.call_oncall('/teams/%s/oncall/manager' % target)
            if not isinstance(result, list):
                stats['oncall_error'] += 1
                return None
            if result:
                return [user['user'] for user in result]
        elif role.startswith('oncall'):
            oncall_type = 'primary' if role == 'oncall' else role[7:]
            result = self.call_oncall('/teams/%s/oncall/%s' % (target, oncall_type))
            if not isinstance(result, list):
                stats['oncall_error'] += 1
                return None
            if result:
                return [user['user'] for user in result]
