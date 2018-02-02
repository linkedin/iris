# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from iris.custom_import import import_custom_module
import logging
logger = logging.getLogger(__name__)


class IrisRoleLookupException(Exception):
    pass


def get_role_lookups(config):
    modules = config.get('role_lookups', [])

    # default to only support user and mailing_list.
    if not modules:
        modules = ['user', 'mailing_list']

    imported_modules = []
    for m in modules:
        try:
            imported_modules.append(
                import_custom_module('iris.role_lookup', m)(config))
            logger.info('Loaded lookup modules: %s', m)
        except Exception:
            logger.exception('Failed to load role lookup module: %s', m)

    return imported_modules
