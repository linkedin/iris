# -*- coding:utf-8 -*-

from .api import construct_falcon_api

app = construct_falcon_api(True, '/tmp/foo', [], 'iris', None, ('localhost', '1234'),
                           [], {})  # noqa
