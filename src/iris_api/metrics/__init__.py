# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from iris_api.custom_import import import_custom_module
import logging
logger = logging.getLogger(__name__)

stats_reset = {}
stats = {}

metrics_provider = None


def get_metrics_provider(config, app_name):
    return import_custom_module('iris_api.metrics', config['metrics'])(config, app_name)


def emit_metrics():
    if metrics_provider:
        metrics_provider.send_metrics(stats)
    stats.update(stats_reset)


def init(config, app_name, default_stats):
    global metrics_provider
    metrics_provider = get_metrics_provider(config, app_name)
    stats_reset.update(default_stats)
    stats.update(stats_reset)
