# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from iris.custom_import import import_custom_module
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
    applications = {application_cls.name: application_cls for application_cls in (import_custom_module('iris.applications', application) for application in application_vendors)}

    vendor_instances = defaultdict(list)
    app_vendor_instances = defaultdict(lambda: defaultdict(list))
    for vendor_config in vendors:
        vendor_cls = import_custom_module('iris.vendors', vendor_config['type'])
        for mode in vendor_cls.supports:
            vendor_instances[mode].append(vendor_cls(copy.deepcopy(vendor_config)))
            for application_name, application_cls in applications.iteritems():
                app_vendor_instances[application_name][mode].append(application_cls(vendor_cls(copy.deepcopy(vendor_config))))

    for mode, instances in vendor_instances.iteritems():
        random.shuffle(instances)
        _vendors_iter[mode] = itertools.cycle(instances)

    for application_name, modes in app_vendor_instances.iteritems():
        for mode_name, instances in modes.iteritems():
            random.shuffle(instances)
            _app_specific_vendors_iter[application_name][mode_name] = itertools.cycle(instances)
        logger.info('Initialized application %s', application_name)


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
