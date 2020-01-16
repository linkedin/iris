# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from iris.custom_import import import_custom_module
from gevent import sleep
import logging
logger = logging.getLogger(__name__)

stats_reset = {}
stats = {}

metrics_provider = None


def get_metrics_provider(config, app_name):
    return import_custom_module('iris.metrics', config['metrics'])(config, app_name)


def emit():
    if metrics_provider:
        metrics_provider.send_metrics(stats)
    stats.update(stats_reset)


# It's expected that you gevent.spawn this after you monkeypatch everything
def emit_forever():
    while True:
        emit()
        sleep(60)


def init(config, app_name, default_stats):
    global metrics_provider
    metrics_provider = get_metrics_provider(config, app_name)
    stats_reset.update(default_stats)
    stats.update(stats_reset)


def add_new_metrics(default_stats):
    stats_reset.update(default_stats)

    # avoid clobbering existing metrics if they are already present
    for key, default_value in default_stats.items():
        stats.setdefault(key, default_value)


def incr(key, inc=1):
    try:
        stats[key] += inc
    except KeyError as e:
        logger.exception('failed incrementing nonexistent metric: %s', e)


def set(key, value):
    stats[key] = value
