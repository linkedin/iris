#!/usr/bin/env python

# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

# -*- coding:utf-8 -*-

import gevent
from gevent.pywsgi import WSGIServer
from gevent.subprocess import call

import time
import fnmatch
import signal
import sys
import os

import logging
logging.basicConfig()

try:
    import gevent_inotifyx as inotify
except ImportError:
    HAS_INOTIFY = False
else:
    HAS_INOTIFY = True


def event_producer(fd, server):
    while True:
        restart = False
        events = inotify.get_events(fd, None)
        for event in events:
            ignore = False
            if call(['git', 'check-ignore', event.name]) == 0 or fnmatch.fnmatch(event.name, '.git/*'):
                ignore = True
                break
            if not ignore:
                print "File changed:", event.name, event.get_mask_description()
                restart = True
        if restart:
            print 'Restarting %s ...\n' % sys.argv
            server.stop(timeout=1)
            server.close()
            print 'Waiting...'
            time.sleep(3)
            print 'Restart.'
            os.execvp(sys.argv[0], sys.argv)


def sigint_handler(sig, frame):
    print 'Caught sigint. Quitting.'
    sys.exit(0)


def main():
    if len(sys.argv) < 2:
        print 'Usage: %s CONFIG_FILE' % sys.argv[0]
        sys.exit(1)

    signal.signal(signal.SIGINT, sigint_handler)

    from iris.api import get_api, load_config_file

    config = load_config_file(sys.argv[1])
    app = get_api(config)

    server = config['server']
    print 'LISTENING: %(host)s:%(port)d' % server
    server = WSGIServer((server['host'], server['port']), app)

    if HAS_INOTIFY:
        fd = inotify.init()

        for dirname, subfolders, _ in os.walk('.'):
            if '.git' in subfolders:
                subfolders.remove('.git')
            inotify.add_watch(fd, dirname, inotify.IN_MODIFY)

        gevent.spawn(event_producer, fd, server)
    else:
        print 'Missing inotify, disable watch support.'
    server.serve_forever()


if __name__ == '__main__':
    main()
