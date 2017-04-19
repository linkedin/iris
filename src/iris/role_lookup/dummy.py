# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import logging
logger = logging.getLogger(__name__)


class dummy(object):
    def __init__(self, config):
        pass

    def get(self, role, target):
        if role == '_invalid_role' or target == '_invalid_user':
            logger.warning('Deliberately returning 0 results for %s:%s', role, target)
            return []
        return ['foo']
