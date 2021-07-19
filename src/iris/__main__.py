# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from gevent.pywsgi import WSGIServer
from iris.api import API
import sys
import logging
import yaml

if __name__ == '__main__':
    config_path = sys.argv[1]
    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)

    app = API(config)
    logging.basicConfig()
    server = config['server']
    print('LISTENING: %(host)s:%(port)d' % server)
    WSGIServer((server['host'], server['port']), app).serve_forever()
