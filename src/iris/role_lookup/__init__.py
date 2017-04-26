# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from iris.custom_import import import_custom_module


def get_role_lookups(config):

    modules = config.get('role_lookups', [])

    # Support old behavior when there is just one role_lookup module configured and the
    # expected implicit user lookup.
    if not modules:
        modules = ['user', config['role_lookup']]

    return [import_custom_module('iris.role_lookup', module)(config) for module in modules]
