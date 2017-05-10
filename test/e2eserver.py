#!/usr/bin/env python
# -*- coding:utf-8 -*-

from gevent import monkey
monkey.patch_all()  # NOQA

from gevent.pywsgi import WSGIServer
import sys
from iris.api import get_api
from iris.config import load_config


if __name__ == '__main__':
    config = load_config(sys.argv[1])
    addr = (config['server']['host'], config['server']['port'])
    print 'Listening on %s...' % (addr,)
    application = get_api(config)
    WSGIServer(addr, application).serve_forever()
