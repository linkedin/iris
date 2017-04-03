# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import pytest
import socket
import requests
import re
from iris.metrics import get_metrics_provider

# We might not have the prometheus library installed.
pytest.importorskip('prometheus_client')


# in case multiple of this test is ran at once, (try to) avoid port conflicts,
# by starting on a random port
def get_free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


listen_port = get_free_port()

config = {
    'metrics': 'prometheus',
    'prometheus': {
        'test': {
            'server_port': listen_port
        }
    }
}


@pytest.fixture(scope='module')
def metrics():
    return get_metrics_provider(config, 'test')


def test_guage(metrics):
    metrics.send_metrics({
        'value1': 100
    })
    data = requests.get('http://localhost:%d/' % listen_port).text
    m = re.search('^test_value1 (\S+)$', data, re.MULTILINE)
    assert m is not None
    assert m.group(1) == '100.0'
