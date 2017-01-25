# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import requests
from requests.exceptions import RequestException
import logging

logger = logging.getLogger()


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

    def team_members(self, team_name):
        result = self.call_oncall('/teams/%s/users' % team_name)
        if not isinstance(result, list):
            return None
        return result

    def team_manager(self, team_name):
        result = self.call_oncall('/teams/%s/rosters/managers' % team_name)
        if not result:
            return None
        return result['users']

    def team_oncall(self, team_name, oncall_type='primary'):
        result = self.call_oncall('/teams/%s/oncall/%s' % (team_name, oncall_type))
        if not result:
            return None
        return [user['username'] for user in result]

    def team_list(self):
        result = self.call_oncall('/teams')
        if not isinstance(result, list):
            return None
        return result
