import falcon
from falcon import HTTPNotFound, HTTPFound, HTTPBadRequest
from falcon.util import uri
from jinja2 import FileSystemLoader
from jinja2.sandbox import SandboxedEnvironment
from webassets import Environment as AssetsEnvironment, Bundle
from webassets.ext.jinja2 import AssetsExtension
from webassets.script import CommandLineEnvironment
import os
import ujson
import requests
import importlib
import logging
import re
import pyqrcode
from iris.ui import auth
from beaker.middleware import SessionMiddleware
from datetime import datetime

logger = logging.getLogger(__name__)

_filename_ascii_strip_re = re.compile(r'[^A-Za-z0-9_.-]')

ui_root = os.environ.get('STATIC_ROOT', os.path.abspath(os.path.dirname(__file__)))


assets_env = AssetsEnvironment(os.path.join(ui_root, 'static'), url='/static')

assets_env.register('jquery_libs', Bundle('js/jquery-3.3.1.min.js', 'js/jquery.dataTables.min.js',
                                          'js/handlebars-4.0.12.min.js', 'js/hopscotch.min.js',
                                          'js/marked.min.js',
                                          output='bundles/jquery.libs.js'))
assets_env.register('bootstrap_libs', Bundle('js/bootstrap.min.js', 'js/typeahead.js',
                                             'js/bootstrap-datetimepicker.js', 'js/moment-timezone.js',
                                             'js/moment-tz-data.js',
                                             output='bundles/bootstrap.libs.js'))
assets_env.register('iris_js', Bundle('js/iris.js', filters='rjsmin', output='bundles/iris.js'))
assets_env.register('css_libs', Bundle('css/bootstrap.min.css', 'css/bootstrap-datetimepicker.css',
                                       'css/jquery.dataTables.min.css', 'css/hopscotch.min.css',
                                       filters='cssmin', output='bundles/libs.css'))

assets_env.register('iris_css', Bundle('css/iris.css', filters='cssmin', output='bundles/iris.css'))

jinja2_env = SandboxedEnvironment(extensions=[AssetsExtension], autoescape=True)
jinja2_env.loader = FileSystemLoader(os.path.join(ui_root, 'templates'))
jinja2_env.assets_environment = assets_env
jinja2_env.filters['tojson'] = ujson.dumps

mimes = {'.css': 'text/css',
         '.jpg': 'image/jpeg',
         '.js': 'text/javascript',
         '.png': 'image/png',
         '.svg': 'image/svg+xml',
         '.ttf': 'application/octet-stream',
         '.woff': 'application/font-woff'}


def hms(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return '%dh %02dm %02ds' % (h, m, s)


jinja2_env.filters['hms'] = hms


default_route = '/incidents'


jinja2_env.globals['default_route'] = default_route
jinja2_env.globals['current_year'] = datetime.now().year


def build_assets():
    CommandLineEnvironment(assets_env, logger).build()


def login_url(req):
    if req.path and req.path != '/login' and req.path != '/logout' and req.path != '/':
        return '/login/?next=%s' % uri.encode_value(req.path)
    else:
        return '/login/'


def flash_message(req, message, message_type):
    session = req.env['beaker.session']
    session['flash_message'] = {'type': message_type, 'message': message}
    session.save()


def get_flash(req):
    session = req.env['beaker.session']
    message = session.pop('flash_message', None)
    if message:
        session.save()
        return message
    else:
        return None


# In many cases, these routes need window.appData populated with various bits of data which
# are only retrievable by going through the API itself. Forge a request locally and keep the
# beaker cookies so the current user can be authenticated. This will go away once each page
# that makes use of window.appData is converted to use ajax for those values instead.
def get_local_api(req, path):
    return requests.get('%s/v0/%s' % (local_api_url, path), cookies=req.cookies).json()


def create_qr_code(qr_base_url, qr_login_url):
    qr_code_content = qr_base_url + ',' + qr_login_url
    qr_object = pyqrcode.create(qr_code_content)
    # create qr code and save it as a svg image
    qr_filename = ui_root + '/static/images/iris-mobile-qr.svg'
    qr_object.svg(qr_filename, scale=8)


# Credit to Werkzeug for implementation
def secure_filename(filename):
    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, ' ')
    filename = str(_filename_ascii_strip_re.sub('', '_'.join(
        filename.split()))).strip('._')
    return filename


class StaticResource(object):
    allow_read_no_auth = True
    frontend_route = False

    def __init__(self, path):
        self.path = path.lstrip('/')

    def on_get(self, req, resp, filename):
        suffix = os.path.splitext(req.path)[1]
        resp.content_type = mimes.get(suffix, 'application/octet-stream')

        filepath = os.path.join(ui_root, self.path, secure_filename(filename))
        try:
            resp.stream = open(filepath, 'rb')
            resp.stream_len = os.path.getsize(filepath)
        except IOError:
            raise HTTPNotFound()


class Index(object):
    allow_read_no_auth = False
    frontend_route = True

    def on_get(self, req, resp):
        raise HTTPFound(default_route)


class Stats(object):
    allow_read_no_auth = True
    frontend_route = True

    def on_get(self, req, resp):
        resp.content_type = 'text/html'
        resp.body = jinja2_env.get_template('stats.html').render(request=req)


class AppStats(object):
    allow_read_no_auth = True
    frontend_route = True

    def on_get(self, req, resp, application):
        resp.content_type = 'text/html'
        resp.body = jinja2_env.get_template('stats.html').render(request=req)


class SingleStats(object):
    allow_read_no_auth = True
    frontend_route = True

    def on_get(self, req, resp, stat_name):
        resp.content_type = 'text/html'
        resp.body = jinja2_env.get_template('singlestat.html').render(request=req)


class Plans(object):
    allow_read_no_auth = False
    frontend_route = True

    def on_get(self, req, resp):
        resp.content_type = 'text/html'
        resp.body = jinja2_env.get_template('plans.html').render(request=req)


class Plan(object):
    allow_read_no_auth = False
    frontend_route = True

    def on_get(self, req, resp, plan):
        resp.content_type = 'text/html'
        resp.body = jinja2_env.get_template('plan.html').render(request=req,
                                                                target_roles=get_local_api(req, 'target_roles'),
                                                                priorities=get_local_api(req, 'priorities'),
                                                                templates=get_local_api(req, 'templates'),
                                                                applications=get_local_api(req, 'applications'))


class Incidents(object):
    allow_read_no_auth = False
    frontend_route = True

    def on_get(self, req, resp):
        resp.content_type = 'text/html'
        resp.body = jinja2_env.get_template('incidents.html').render(request=req,
                                                                     applications=get_local_api(req, 'applications'))


class Incident(object):
    allow_read_no_auth = False
    frontend_route = True

    def on_get(self, req, resp, incident):
        resp.content_type = 'text/html'
        resp.body = jinja2_env.get_template('incident.html').render(request=req)


class Messages(object):
    allow_read_no_auth = False
    frontend_route = True

    def on_get(self, req, resp):
        resp.content_type = 'text/html'
        resp.body = jinja2_env.get_template('messages.html').render(request=req,
                                                                    applications=get_local_api(req, 'applications'),
                                                                    priorities=get_local_api(req, 'priorities'))


class Message(object):
    allow_read_no_auth = False
    frontend_route = True

    def on_get(self, req, resp, message):
        resp.content_type = 'text/html'
        resp.body = jinja2_env.get_template('message.html').render(request=req)


class Templates(object):
    allow_read_no_auth = False
    frontend_route = True

    def on_get(self, req, resp):
        resp.content_type = 'text/html'
        resp.body = jinja2_env.get_template('templates.html').render(request=req)


class Template(object):
    allow_read_no_auth = False
    frontend_route = True

    def on_get(self, req, resp, template):
        resp.content_type = 'text/html'
        resp.body = jinja2_env.get_template('template.html').render(request=req,
                                                                    modes=get_local_api(req, 'modes'),
                                                                    applications=get_local_api(req, 'applications'))


class Applications(object):
    allow_read_no_auth = False
    frontend_route = True

    def on_get(self, req, resp):
        resp.content_type = 'text/html'
        resp.body = jinja2_env.get_template('applications.html').render(request=req,
                                                                        applications=get_local_api(req, 'applications'))


class Application(object):
    allow_read_no_auth = False
    frontend_route = True

    def on_get(self, req, resp, application):
        resp.content_type = 'text/html'
        resp.body = jinja2_env.get_template('application.html').render(request=req,
                                                                       applications=get_local_api(req, 'applications'),
                                                                       priorities=get_local_api(req, 'priorities'),
                                                                       modes=get_local_api(req, 'modes') + ['drop'])


class Unsubscribe(object):
    allow_read_no_auth = False
    frontend_route = True

    def on_get(self, req, resp, application):
        resp.content_type = 'text/html'
        resp.body = jinja2_env.get_template('unsubscribe.html').render(request=req,
                                                                       priorities=get_local_api(req, 'priorities'))


class Login():
    allow_read_no_auth = False
    frontend_route = True

    def __init__(self, auth_manager, debug):
        self.auth_manager = auth_manager
        self.debug = debug

    def on_get(self, req, resp):
        resp.content_type = 'text/html'
        resp.body = jinja2_env.get_template('login.html').render(request=req,
                                                                 path='login',
                                                                 last_flash=get_flash(req))

    def on_post(self, req, resp):
        form_body = uri.parse_query_string(req.context['body'].decode('utf-8'))

        try:
            username = form_body['username']
            password = form_body['password']
        except KeyError:
            raise HTTPFound('/login')

        if not auth.valid_username(username):
            logger.warning('Tried to login with invalid username %s', username)
            if self.debug:
                flash_message(req, 'Invalid username', 'danger')
            else:
                flash_message(req, 'Invalid credentials', 'danger')
            raise HTTPFound('/login')

        if self.auth_manager.authenticate(username, password):
            logger.info('Successful login for %s', username)
            auth.login_user(req, username)
        else:
            logger.warning('Failed login for %s', username)
            flash_message(req, 'Invalid credentials', 'danger')
            raise HTTPFound('/login')

        # Remove newlines to prevent HTTP request splitting
        url = req.get_param('next', default='').replace('\n', '')

        if not url or url.startswith('/'):
            raise HTTPFound(url or default_route)
        else:
            raise HTTPBadRequest('Invalid next parameter', '')


class Logout():
    allow_read_no_auth = False
    frontend_route = True

    def on_get(self, req, resp):
        auth.logout_user(req)
        raise HTTPFound('/login')


class User():
    allow_read_no_auth = False
    frontend_route = True

    def on_get(self, req, resp):
        resp.content_type = 'text/html'
        resp.body = jinja2_env.get_template('user.html').render(request=req,
                                                                modes=get_local_api(req, 'modes'),
                                                                priorities=get_local_api(req, 'priorities'),
                                                                applications=get_local_api(req, 'applications'))


class Qr(object):
    allow_read_no_auth = True
    frontend_route = True

    def __init__(self, qr_base_url, qr_login_url):
        self.qr_base_url = qr_base_url
        self.qr_login_url = qr_login_url

    def on_get(self, req, resp):
        resp.content_type = 'text/html'
        resp.body = jinja2_env.get_template('qr.html').render(base=self.qr_base_url, login=self.qr_login_url)


class JinjaValidate():
    allow_read_no_auth = False
    frontend_route = True

    def on_post(self, req, resp):
        form_body = uri.parse_query_string(req.context['body'].decode('utf-8'))

        try:
            template_subject = form_body['templateSubject']
            template_body = form_body['templateBody']
            application = form_body['application']
        except KeyError:
            raise HTTPBadRequest('Missing keys from post body', '')

        if not application:
            resp.body = ujson.dumps({'error': 'No application found'})
            resp.status = falcon.HTTP_400
            return

        app_json = get_local_api(req, 'applications/%s' % application)
        sample_context_str = app_json.get('sample_context')
        if not sample_context_str:
            resp.body = ujson.dumps({'error': 'Missing sample_context from application config'})
            resp.status = falcon.HTTP_400
            logger.error('Missing sample context for app %s', application)
            return

        try:
            sample_context = ujson.loads(sample_context_str)
        except Exception:
            resp.body = ujson.dumps({'error': 'Invalid application sample_context'})
            resp.status = falcon.HTTP_400
            logger.exception('Bad sample context for app %s', application)
            return

        # TODO: also move iris meta var to api
        iris_sample_context = {
            "message_id": 5456900,
            "target": "user",
            "priority": "Urgent",
            "application": "Autoalerts",
            "plan": "default plan",
            "plan_id": 1843,
            "incident_id": 178293332,
            "template": "default template"
        }
        sample_context['iris'] = iris_sample_context

        environment = SandboxedEnvironment()

        try:
            subject_template = environment.from_string(template_subject)
            body_template = environment.from_string(template_body)
        except Exception as e:
            resp.body = ujson.dumps({'error': str(e), 'lineno': e.lineno})
            resp.status = falcon.HTTP_400
            return

        try:
            rendered_subject = subject_template.render(sample_context),
            rendered_body = body_template.render(sample_context)
        except Exception as e:
            resp.body = ujson.dumps({'error': str(e)})
            resp.status = falcon.HTTP_400
            return

        resp.body = ujson.dumps({
            'template_subject': rendered_subject,
            'template_body': rendered_body
        })


def init(config, app):
    global local_api_url
    logger.info('Web asset root: "%s"', ui_root)
    auth_module = config.get('auth', {'module': 'iris.ui.auth.noauth'})['module']
    auth = importlib.import_module(auth_module)
    auth_manager = getattr(auth, 'Authenticator')(config)
    qr_base_url = config.get('qr_base_url')
    qr_login_url = config.get('qr_login_url')

    debug = config['server'].get('disable_auth', False) is True
    local_api_url = config['server'].get('local_api_url', 'http://localhost:16649')

    app.add_route('/static/bundles/{filename}', StaticResource('/static/bundles'))
    app.add_route('/static/images/{filename}', StaticResource('/static/images'))
    app.add_route('/static/fonts/{filename}', StaticResource('/static/fonts'))
    app.add_route('/', Index())
    app.add_route('/stats', Stats())
    app.add_route('/stats/{application}', AppStats())
    app.add_route('/singlestats/{stat_name}', SingleStats())
    app.add_route('/plans/', Plans())
    app.add_route('/plans/{plan}', Plan())
    app.add_route('/incidents/', Incidents())
    app.add_route('/incidents/{incident}', Incident())
    app.add_route('/messages/', Messages())
    app.add_route('/messages/{message}', Message())
    app.add_route('/templates/', Templates())
    app.add_route('/templates/{template}', Template())
    app.add_route('/applications/', Applications())
    app.add_route('/applications/{application}', Application())
    app.add_route('/login/', Login(auth_manager, debug))
    app.add_route('/logout/', Logout())
    app.add_route('/user/', User())
    app.add_route('/validate/jinja', JinjaValidate())
    app.add_route('/unsubscribe/{application}', Unsubscribe())

    if(qr_base_url and qr_login_url):
        create_qr_code(qr_base_url, qr_login_url)
        app.add_route('/qr', Qr(qr_base_url, qr_login_url))

    # Configuring the beaker middleware mutilates the app object, so do it
    # at the end, after we've added all routes/sinks for the entire iris
    # app.
    session_opts = {
        'session.type': 'cookie',
        'session.cookie_expires': True,
        'session.key': 'iris-auth',
        'session.encrypt_key': config['user_session']['encrypt_key'],
        'session.validate_key': config['user_session']['sign_key'],
        'session.secure': not (config['server'].get('disable_auth', False) or config['server'].get('allow_http', False)),
        'session.httponly': True,
        'session.crypto_type': 'cryptography',
        'session.samesite': 'Lax'
    }
    app = SessionMiddleware(app, session_opts)

    return app
