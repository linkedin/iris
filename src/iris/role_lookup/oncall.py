# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import requests
import logging
from iris.metrics import stats
import oncallclient
from iris.role_lookup import IrisRoleLookupException

logger = logging.getLogger(__name__)


class oncall(object):
    def __init__(self, config):
        headers = requests.utils.default_headers()
        headers['User-Agent'] = 'iris role lookup (%s)' % headers.get('User-Agent')
        app = config.get('oncall-app', '')
        key = config.get('oncall-key', '')
        self.requests = requests.session()
        if app and key:
            self.requests.auth = oncallclient.OncallAuth(app, key)
        oncallclient.OncallAuth(app, key)
        self.requests.headers = headers
        self.endpoint = config['oncall-api'] + '/api/v0'

    def call_oncall(self, url, expected_type):
        url = str(self.endpoint + url)
        try:
            r = self.requests.get(url)
        except Exception:
            stats['oncall_error'] += 1
            msg = 'Failed hitting oncall-api for url "%s"' % url
            logger.exception(msg)
            raise IrisRoleLookupException(msg)

        if r.status_code != 200:
            # 422 from Oncall indicates nonexistent team from a misconfigured plan; return None for this case
            if r.status_code == 422:
                logger.warning('422 for url "%s", likely invalid plan' % url)
                return None
            else:
                stats['oncall_error'] += 1
                msg = 'Invalid response from oncall-api for URL "%s". Code: %s. Content: "%s"' \
                    % (url, r.status_code, r.content)
                logger.error(msg)
                raise IrisRoleLookupException(msg)

        try:
            data = r.json()
            if not isinstance(data, expected_type):
                stats['oncall_error'] += 1
                msg = 'Invalid data recieved from oncall-api for URL %s' % url
                logger.error(msg)
                raise IrisRoleLookupException(msg)
            return data
        except ValueError:
            stats['oncall_error'] += 1
            msg = 'Failed decoding json from oncall-api. URL: "%s" Code: %s' % (url, r.status_code)
            logger.exception(msg)
            raise IrisRoleLookupException(msg)

    def get(self, role, target):
        if role == 'team':
            result = self.call_oncall('/teams/%s/rosters' % target, dict)
            user_list = []
            if result:
                for roster in result:
                    for user in result[roster]['users']:
                        user_list.append(user['name'])
                return user_list
            else:
                return None
        elif role == 'manager':
            result = self.call_oncall('/teams/%s/oncall/manager' % target, list)
            if result:
                return [user['user'] for user in result]
            else:
                return None
        # "oncall" role maps to primary, otherwise grab shift type from the role suffix (eg "oncall-shadow")
        elif role.startswith('oncall'):
            oncall_type = 'primary' if role == 'oncall' else role[7:]
            result = self.call_oncall('/teams/%s/oncall/%s' % (target, oncall_type), list)
            if result:
                return [user['user'] for user in result]
            else:
                return None
        # Other roles can't be handled by this plugin; return None.
        else:
            return None
