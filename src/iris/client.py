import requests
import base64
import hashlib
import hmac
import time
import logging

logger = logging.getLogger(__name__)
logging.getLogger('requests').setLevel(logging.WARNING)


class IrisAuth(requests.auth.AuthBase):
    def __init__(self, app, key):
        self.header = 'hmac %s:' % app
        key = key if isinstance(key, bytes) else key.encode('utf8')
        self.HMAC = hmac.new(key, b'', hashlib.sha512)

    def __call__(self, request):
        HMAC = self.HMAC.copy()
        path = request.path_url
        method = request.method
        body = request.body or ''
        window = int(time.time()) // 5
        text = '%s %s %s %s' % (window, method, path, body)
        text = text.encode('utf8')
        HMAC.update(text)
        digest = base64.urlsafe_b64encode(HMAC.digest())
        self.header = self.header if isinstance(self.header, bytes) else self.header.encode('utf8')
        request.headers['Authorization'] = self.header + digest
        return request


class IrisClient(requests.Session):
    def __init__(self, base, version=0, iris_app=None, iris_app_key=None):
        super(IrisClient, self).__init__()
        self.url = base + '/v%d/' % version
        adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100)
        self.mount('http://', adapter)
        self.mount('https://', adapter)

        if iris_app and iris_app_key:
            self.auth = IrisAuth(iris_app, iris_app_key)
            logger.info('Initializing iris api client with auth using app %s', iris_app)
        else:
            logger.warning('Initializing iris api client without auth')

    def get(self, path, *args, **kwargs):
        return super(IrisClient, self).get(self.url + path, *args, **kwargs)

    def post(self, path, *args, **kwargs):
        return super(IrisClient, self).post(self.url + path, *args, **kwargs)

    def put(self, path, *args, **kwargs):
        return super(IrisClient, self).put(self.url + path, *args, **kwargs)
