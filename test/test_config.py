# -*- coding:utf-8 -*-
# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.


def test_load_config(mocker):
    import os
    from tempfile import NamedTemporaryFile
    from iris.config import load_config

    mocker.patch.dict(os.environ, {'IRIS_CFG_DB_USER': 'iris_dev'})

    with NamedTemporaryFile() as temp_config:
        temp_config.write(b'''
db:
  conn:
    kwargs:
      scheme: mysql+pymysql
      user: iris
      password: iris
      host: 127.0.0.1
      database: iris
      charset: utf8
    str: "%(scheme)s://%(user)s:%(password)s@%(host)s/%(database)s?charset=%(charset)s"
''')
        temp_config.flush()
        config = load_config(temp_config.name)
        assert config['db']['conn']['kwargs']['user'] == 'iris_dev'
