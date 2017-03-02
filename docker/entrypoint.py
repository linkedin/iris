# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import yaml
import subprocess
import os
import socket
import time
import sys
from glob import glob

dbpath = '/home/iris/db'
configfile = '/home/iris/config/config.yaml'
initializedfile = '/home/iris/db_initialized'


def load_sqldump(config, sqlfile):
    print 'Importing %s...' % sqlfile
    with open(sqlfile) as h:
        cmd = ['/usr/bin/mysql', '-h', config['host'], '-u', config['user'], '-p' + config['password'], config['database']]
        proc = subprocess.Popen(cmd, stdin=h)
        proc.communicate()

        if proc.returncode == 0:
            print 'DB successfully loaded ' + sqlfile
            return True
        else:
            print 'Ran into problems during DB bootstrap. IRIS will likely not function correctly. mysql exit code: %s for %s' % (proc.returncode, sqlfile)
            return False


def wait_for_mysql(config):
    db_address = (config['host'], 3306)

    tries = 0
    while True:
        try:
            sock = socket.socket()
            sock.connect(db_address)
            sock.close()
            break
        except socket.error:
            if tries > 20:
                print 'Waited too long for DB to come up. Bailing.'
                sys.exit(1)

            print 'DB not up yet. Waiting a few seconds..'
            time.sleep(2)
            tries += 1
            continue


def initialize_mysql_schema(config):
    print 'Initializing Iris database'

    load_sqldump(config, os.path.join(dbpath, 'schema_0.sql'))

    for f in glob(os.path.join(dbpath, 'patches', '*.sql')):
        load_sqldump(config, f)

    load_sqldump(config, os.path.join(dbpath, 'dummy_data.sql'))

    with open(initializedfile, 'w'):
        print 'Wrote %s so we don\'t bootstrap db again' % initializedfile


def main():
    if not os.path.exists(configfile):
        print 'Config file does not exist (%s)' % configfile
        sys.exit(1)

    if not os.path.exists(dbpath):
        print 'DB schemas folder does not exist (%s)' % dbpath
        sys.exit(1)

    with open(configfile) as h:
        try:
            config = yaml.safe_load(h)['db']['conn']['kwargs']
        except KeyError as e:
            print 'Confg file missing keys: %s' % e
            sys.exit(1)

    # It often takes several seconds for MySQL to start up. iris-api dies upon start
    # if it can't immediately connect to MySQL, so we have to wait for it.
    wait_for_mysql(config)

    if 'DOCKER_DB_BOOTSTRAP' in os.environ:
        if not os.path.exists(initializedfile):
            initialize_mysql_schema(config)

    os.execv('/usr/bin/uwsgi', ['', '--yaml', '/home/iris/daemons/uwsgi.yaml:prod'])


if __name__ == '__main__':
    main()
