# -*- coding:utf-8 -*-
# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import sys
import os
import logging
from importlib import import_module
import yaml

logger = logging.getLogger(__name__)


def load_config_file(path=None):
    ''' Get config from path to file, defaulting to cli arg. This can easily be monkey patched. '''
    if not path:
        if len(sys.argv) <= 1:
            print('ERROR: missing config file.')
            print('usage: %s API_CONFIG_FILE' % sys.argv[0])
            sys.exit(1)
        path = sys.argv[1]

    with open(path) as h:
        return yaml.safe_load(h)


def process_config_hook(config):
    ''' Examine config dict for hooks and run them if present '''
    if 'init_config_hook' in config:
        try:
            module = config['init_config_hook']
            logger.info('Bootstrapping config using %s', module)
            getattr(import_module(module), module.split('.')[-1])(config)
        except ImportError:
            logger.exception('Failed loading config hook %s', module)

    return config


def load_config(path=None):
    '''
      Generate configs for iris in the following steps:

        * reads config from yaml file by calling `load_config_file()`.
        * reads more config values from environment variables and use them to
          override values from the config file.
        * pass config through process_config_hook(). It looks for a key called
          init_config_hook in the config, which is the name of a module to call
          which can tweak the config further.

      load_config_file() can be monkey patched, in which case this config
      loading functionality can be customized further.
    '''
    config = load_config_file(path)
    if not config:
        sys.exit('Failed to load config from ' + path)

    if 'IRIS_CFG_DB_HOST' in os.environ:
        config['db']['conn']['kwargs']['host'] = os.environ['IRIS_CFG_DB_HOST']
    if 'IRIS_CFG_DB_USER' in os.environ:
        config['db']['conn']['kwargs']['user'] = os.environ['IRIS_CFG_DB_USER']
    if 'IRIS_CFG_DB_PASSWORD' in os.environ:
        config['db']['conn']['kwargs']['password'] = os.environ['IRIS_CFG_DB_PASSWORD']
    return process_config_hook(config)
