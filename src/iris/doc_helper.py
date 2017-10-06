# -*- coding:utf-8 -*-

from .api import construct_falcon_api

config = {'debug': True,
          'server': {},
          'healthcheck_path': '/tmp/foo',
          'allowed_origins': [],
          'sender': {'sender_app': 'iris', 'host': 'localhost', 'port': 1234}
          }
app = construct_falcon_api(config)  # noqa
