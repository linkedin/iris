# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import setuptools

setuptools.setup(
    name='iris',
    version='0.14.0',
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
        # plugin deps
        'prometheus_client',
        'influxdb',
    ],
    entry_points={
        'console_scripts': [
            'iris-api = iris.bin.run_server:main',
            'iris = iris.bin.run_server:main',
            'iris-sender = iris.bin.sender:main',
            'iris-sync-targets = iris.bin.sync_targets:main',
            'iris_ctl = iris.bin.iris_ctl:main',
            'build_assets = iris.bin.ui_build_assets:main',
        ]
    }
)
