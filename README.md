[![Build Status](https://travis-ci.org/linkedin/iris-api.svg?branch=master)](https://travis-ci.org/linkedin/iris-api)
[![License](https://img.shields.io/badge/License-BSD%202--Clause-orange.svg)](https://opensource.org/licenses/BSD-2-Clause)

Iris API
========

Iris API core and sender service


Setup database
--------------

1. remove `ONLY_FULL_GROUP_BY` from MySQL config `sql_mode`
1. create mysql schema: `mysql -u USER -p < ./db/schema_0.sql`
1. import dummy data: `mysql -u USER -p -o iris < ./db/dummy_data.sql`

`dummy_data.sql` contains the following entities:
  * user `demo`
  * team `demo_team`
  * application `Autoalerts` with key: `a7a9d7657ac8837cd7dfed0b93f4b8b864007724d7fa21422c24f4ff0adb2e49`


Setup dev environment
---------------------

1. create & source your virtualenv
1. run `python setup.py develop`
1. run `pip install -r dev_requirements.txt`
1. edit ./configs/config.dev.yaml to setup database credential and other settings


Run API server
--------------

```bash
make serve
```


Run sender
---------

```bash
iris-sender configs/config.dev.yaml
```


Tests
-----

Run tests:

```bash
make test  # all tests, e2e + unit
make e2e  # e2e tests
make unit  # unit tests
```

Generate test coverage reports:

```bash
make e2e-cov
make unit-cov
```


Adding new plugins
------------------

1. create the plugin file under `src/iris_api/plugis` dir
1. edit `src/iris_api/plugins/__init__.py` to add plugin module to `__all__` list
