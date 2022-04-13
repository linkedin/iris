[Iris](http://iris.claims) [![Build Status](https://circleci.com/gh/linkedin/iris.svg?style=shield)](https://circleci.com/gh/linkedin/iris) [![License](https://img.shields.io/badge/License-BSD%202--Clause-orange.svg)](https://opensource.org/licenses/BSD-2-Clause) [![Gitter chat](https://badges.gitter.im/irisoncall/Lobby.png)](https://gitter.im/irisoncall/Lobby) [![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/linkedin/iris)
========

Iris core, API, UI and sender service. For third-party integration support, see [iris-relay](https://github.com/linkedin/iris-relay), a stateless proxy designed to sit at the edge of a production network and allow external traffic to pass through. We also have an Iris mobile app for iOS/Android, at the [iris-mobile](https://github.com/linkedin/iris-mobile) repo.

<p align="center"><img src="https://github.com/linkedin/iris/raw/master/docs/source/_static/demo.png" width="600"></p>


Setup database
--------------

1. remove `ONLY_FULL_GROUP_BY` from MySQL config `sql_mode` or run mysqld in permisive mode (i.e. `--sql_mode=''`)
1. create mysql schema: `mysql -u USER -p < ./db/schema_0.sql`  (WARNING: This will drop any existing tables)
1. import dummy data: `mysql -u USER -p -o iris < ./db/dummy_data.sql`

`dummy_data.sql` contains the following entities:
  * user `demo` with password `demo`
  * team `demo_team`
  * application `Autoalerts` with key: `a7a9d7657ac8837cd7dfed0b93f4b8b864007724d7fa21422c24f4ff0adb2e49`


Setup dev environment
---------------------

1. create & source your virtualenv
1. install build dependencies: `libssl-dev libxml2-dev libxslt1-dev libsasl2-dev python-dev libldap2-dev`
1. run `pip install -e '.[dev,kazoo]'`
1. edit ./configs/config.dev.yaml to setup database credential and other settings

To install iris with extra features, you can pass in feature flag with pip:

```bash
pip install -e '.[prometheus]'
```

For list of extra features, please see `extras_require` setting in `setup.py`.


Run everything
--------------

```bash
forego start
```


Run web server
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

1. create the plugin file under `src/iris/plugins` dir
1. edit `src/iris/plugins/__init__.py` to add plugin module to `__all__` list
