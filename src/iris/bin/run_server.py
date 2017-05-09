#!/usr/bin/env python

# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import sys
import multiprocessing
import gunicorn.app.base
from gunicorn.six import iteritems
import iris
import iris.config
import iris.api


class StandaloneApplication(gunicorn.app.base.BaseApplication):

    def __init__(self, options=None):
        self.options = options or {}
        super(StandaloneApplication, self).__init__()

    def load_config(self):
        config = {key: value for key, value in iteritems(self.options)
                  if key in self.cfg.settings and value is not None}
        for key, value in iteritems(config):
            self.cfg.set(key.lower(), value)

    def load(self):
        reload(iris)
        reload(iris.config)
        reload(iris.api)
        config = iris.config.load_config(sys.argv[1])
        return iris.api.get_api(config)


def main():
    config = iris.config.load_config(sys.argv[1])
    server = config['server']

    options = {
        'preload_app': False,
        'reload': True,
        'bind': '%s:%s' % (server['host'], server['port']),
        'worker_class': 'gevent',
        'accesslog': '-',
        'workers': (multiprocessing.cpu_count() * 2) + 1
    }

    gunicorn_server = StandaloneApplication(options)
    gunicorn_server.run()


if __name__ == '__main__':
    main()
