# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import setuptools
import re

with open('src/iris/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE).group(1)

setuptools.setup(
    name='iris',
    version=version,
    package_dir={'': 'src'},
    packages=setuptools.find_packages('src'),
    include_package_data=True,
    install_requires=[
        'streql==3.0.2',
        'dnspython==1.14.0',
        'phonenumbers==7.4.1',
        'twilio==4.5.0',
        'google-api-python-client==1.4.2',
        'oauth2client==1.4.12',
        'slackclient==0.16',
        'PyYAML==3.11',
        'gevent==1.1.2',
        'falcon==1.1.0',
        'falcon-cors==1.1.2',
        'ujson==1.35',
        'requests==2.9.1',
        'PyMySQL==0.7.2',
        'SQLAlchemy==1.0.11',
        'Jinja2==2.8',
        'importlib==1.0.3',
        'Markdown==2.4.1',
        'click==6.6',
        'msgpack-python==0.4.5',
        'cssmin==0.2.0',
        'pycrypto==2.6.1',
        'beaker==1.8.0',
        'webassets==0.12.0',
        'python-ldap==2.4.9',
        'exchangelib==1.10.0',
        'PyQRCode==1.2.1',
        'pypng==0.0.18',
        'setproctitle==1.1.8',
    ],
    extras_require={
        'kazoo': ['kazoo==2.3.1'],
        # plugin deps
        'influxdb': ['influxdb'],
        'prometheus': ['prometheus_client'],
        'dev': [
            'gunicorn',
            'Sphinx==1.5.6',
            'sphinxcontrib-httpdomain',
            'sphinx_rtd_theme',
            # test deps
            'mock==2.0.0',
            'pytest==3.0.5',
            'pytest-mock==1.5.0',
            'pytest-cov',
            'flake8',
            'tox',
            'requests-mock==1.1.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'iris-dev = iris.bin.run_server:main',
            'iris = iris.bin.run_server:main',
            'iris-sender = iris.bin.sender:main',
            'iris-owa-sync = iris.bin.owasync:main',
            'iris-sync-targets = iris.bin.sync_targets:main',
            'iris_ctl = iris.bin.iris_ctl:main',
            'build_assets = iris.bin.ui_build_assets:main',
        ]
    }
)
