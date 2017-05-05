#!/usr/bin/env python

# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import sys
import multiprocessing
import gunicorn.app.base
from gunicorn.six import iteritems
from iris.config import load_config
from iris.api import get_api


class StandaloneApplication(gunicorn.app.base.BaseApplication):

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super(StandaloneApplication, self).__init__()

    def load_config(self):
        config = {key: value for key, value in iteritems(self.options)
                  if key in self.cfg.settings and value is not None}
        for key, value in iteritems(config):
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def main():
    config = load_config(sys.argv[1])
    server = config['server']

    options = {
        'reload': True,
        'bind': '%s:%s' % (server['host'], server['port']),
        'worker_class': 'gevent',
        'accesslog': '-',
        'workers': (multiprocessing.cpu_count() * 2) + 1
    }

    gunicorn_server = StandaloneApplication(get_api(config), options)
    gunicorn_server.run()
