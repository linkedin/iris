# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from iris.custom_import import import_custom_module
from collections import defaultdict
import logging
import itertools
import random
import copy
logger = logging.getLogger(__name__)


class IrisVendorException(Exception):
    pass


class IrisVendorManager():

    def __init__(self, vendors, application_vendors):
        self.max_tries_per_message = 5
        self.vendors_iter = {}
        self.app_specific_vendors_iter = defaultdict(dict)
        self.all_vendor_instances = []

        applications = {}

        for application in application_vendors:
            try:
                application_cls = import_custom_module('iris.applications', application)
            except ImportError:
                logger.exception('Failed importing application %s', application)
                continue

            try:
                applications[application_cls.name] = application_cls
            except AttributeError:
                logger.exception('Failed loading name of custom application %s', application)
                continue

        vendor_instances = defaultdict(list)
        app_vendor_instances = defaultdict(lambda: defaultdict(list))
        for vendor_config in vendors:
            vendor_cls = import_custom_module('iris.vendors', vendor_config['type'])
            for mode in vendor_cls.supports:
                vendor_instance = vendor_cls(copy.deepcopy(vendor_config))
                vendor_instances[mode].append(vendor_instance)
                for application_name, application_cls in applications.items():
                    app_vendor_instances[application_name][mode].append(application_cls(vendor_instance))

        for mode, instances in vendor_instances.items():
            random.shuffle(instances)
            self.all_vendor_instances += instances
            self.vendors_iter[mode] = itertools.cycle(instances)

        for application_name, modes in app_vendor_instances.items():
            for mode_name, instances in modes.items():
                random.shuffle(instances)
                self.app_specific_vendors_iter[application_name][mode_name] = itertools.cycle(instances)

    def send_message(self, message):
        for tries, vendor in enumerate(self.app_specific_vendors_iter.get(message.get('application'), self.vendors_iter)[message['mode']]):
            if tries > self.max_tries_per_message:
                logger.warning('Exhausted %d tries for message %s', tries, message)
                break
            logger.debug('Attempting %s send using vendor %s', message['mode'], vendor)
            try:
                return vendor.send(message)
            except Exception:
                logger.exception('Sending %s with vendor %s failed', message, vendor)
                continue

        raise IrisVendorException('All %s vendors failed for %s' % (message['mode'], message))

    def cleanup(self):
        for vendors in self.all_vendor_instances:
            cleanup_method = getattr(vendors, 'cleanup', None)
            if cleanup_method:
                cleanup_method()
