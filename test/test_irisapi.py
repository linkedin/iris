# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

"""Tests for iris-api."""
import falcon.testing
import iris_api.cache
from iris_api.api import ReqBodyMiddleware, AuthMiddleware, Healthcheck
import time
import hmac
import hashlib
import base64
from mock import patch, mock_open


class TestCommand(falcon.testing.TestCase):
    def test_parse_response(self):
        from iris_api.utils import parse_response
        with patch('iris_api.utils.db'):
            msg_id, cmd = parse_response('123 Claim', 'sms', '123-456-7890')
            self.assertEqual(msg_id, '123')
            self.assertEqual(cmd, 'claim')

            msg_id, cmd = parse_response('Claim 123', 'sms', '123-456-7890')
            self.assertEqual(msg_id, '123')
            self.assertEqual(cmd, 'claim')

            msg_id, cmd = parse_response('claim 123', 'sms', '123-456-7890')
            self.assertEqual(msg_id, '123')
            self.assertEqual(cmd, 'claim')


class TestHealthcheck(falcon.testing.TestCase):
    def test_healthcheck(self):
        with patch('__builtin__.open', mock_open(read_data='GOOD')) as m:
            self.api.add_route('/healthcheck', Healthcheck('healthcheck_path'))
            result = self.simulate_get(path='/healthcheck')
            m.assert_called_once_with('healthcheck_path')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, 'GOOD')


class TestAuth(falcon.testing.TestCase):

    class DummyResource(object):
        allow_read_only = False

        def on_get(self, req, resp):
            resp.status = falcon.HTTP_200
            resp.body = 'Hello world'

    def test_auth(self):
        iris_api.cache.applications = {'app': {'key': 'key'}}
        api = falcon.API(middleware=[ReqBodyMiddleware(), AuthMiddleware()])
        dummy = self.DummyResource()
        api.add_route('/foo/bar', dummy)
        self.api = api

        window = int(time.time()) // 5
        text = '%s %s %s %s' % (window, 'GET', '/foo/bar', '')
        HMAC = hmac.new('key', text, hashlib.sha512)
        digest = base64.urlsafe_b64encode(HMAC.digest())
        auth = 'hmac app:%s' % digest
        result = self.simulate_get(path='/foo/bar', headers={'Authorization': auth})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, 'Hello world')

        # Test query string
        window = int(time.time()) // 5
        text = '%s %s %s %s' % (window, 'GET', '/foo/bar?baz=123', '')
        HMAC = hmac.new('key', text, hashlib.sha512)
        digest = base64.urlsafe_b64encode(HMAC.digest())
        auth = 'hmac app:%s' % digest
        result = self.simulate_get(path='/foo/bar', query_string='baz=123', headers={'Authorization': auth})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, 'Hello world')

        # Test trailng slash
        window = int(time.time()) // 5
        text = '%s %s %s %s' % (window, 'GET', '/foo/bar/', '')
        HMAC = hmac.new('key', text, hashlib.sha512)
        digest = base64.urlsafe_b64encode(HMAC.digest())
        auth = 'hmac app:%s' % digest
        result = self.simulate_get(path='/foo/bar/', headers={'Authorization': auth})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, 'Hello world')

        # Test no auth header
        result = self.simulate_get(path='/foo/bar')
        self.assertEqual(result.status_code, 401)

        # Test bad auth header
        result = self.simulate_get(path='/foo/bar',
                                   headers={'Authorization': 'foo' + auth})
        self.assertEqual(result.status_code, 401)

        # Test read only
        dummy.allow_read_only = True
        result = self.simulate_get(path='/foo/bar')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, 'Hello world')
