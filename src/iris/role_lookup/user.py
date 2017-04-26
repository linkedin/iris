# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import logging
logger = logging.getLogger(__name__)


class user(object):
    def __init__(self, config):
        pass

    def get(self, role, target):
        if role == 'user':
            return [target]
        else:
            return None
