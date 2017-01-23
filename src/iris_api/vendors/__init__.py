# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from iris_api.custom_import import import_custom_module
from collections import defaultdict
import logging
import itertools
import random
import copy
logger = logging.getLogger(__name__)

_max_tries_per_message = 5
_vendors_iter = {}
_app_specific_vendors_iter = defaultdict(dict)


class IrisVendorException(Exception):
    pass


def init_vendors(vendors, application_vendors):
    vendor_instances = defaultdict(list)
    for vendor in vendors:
        instance = import_custom_module('iris_api.vendors', vendor['type'])(vendor)
        for mode in instance.supports:
            vendor_instances[mode].append(instance)

    for mode, instances in vendor_instances.iteritems():
        random.shuffle(instances)
        _vendors_iter[mode] = itertools.cycle(instances)

    # Create application-specific versions of those vendors
    for application in application_vendors:
        application_cls = import_custom_module('iris_api.applications', application)
        application_name = application_cls.name

        logger.info('Loaded application %s', application_name)

        for mode, instances in vendor_instances.iteritems():
            _app_specific_vendors_iter[application_name][mode] = itertools.cycle(application_cls(copy.deepcopy(instance)) for instance in instances)


def send_message(message):
    for tries, vendor in enumerate(_app_specific_vendors_iter.get(message.get('application'), _vendors_iter)[message['mode']]):
        if tries > _max_tries_per_message:
            logger.warning('Exhausted %d tries for message %s', tries, message)
            break
        logger.debug('Attempting %s send using vendor %s', message['mode'], vendor)
        try:
            return vendor.send(message)
        except Exception:
            logger.exception('Sending %s with vendor %s failed', message, vendor)
            continue

    raise IrisVendorException('All %s vendors failed for %s' % (message['mode'], message))
