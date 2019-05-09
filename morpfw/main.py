import importlib
import reg
import morepath
from .app import SQLApp, Session, BaseApp
from .authn.pas.user.model import UserCollection, UserSchema, UserModel
from .authn.pas.group.model import GroupSchema, GroupModel
from .sql import Base
import os
from zope.sqlalchemy import register as register_session
from more.basicauth import BasicAuthIdentityPolicy
from .exc import ConfigurationError
import transaction
import sqlalchemy
from celery import Celery
import yaml
import copy
import tempfile
import multiprocessing
import subprocess

default_settings = open(os.path.join(
    os.path.dirname(__file__), 'default_settings.yml')).read()
default_settings = default_settings.replace(r'%(here)s', os.getcwd())
default_settings = yaml.load(default_settings)


@reg.dispatch(reg.match_class('app', lambda app, *args, **kwargs: app))
def create_app(app, settings, scan=True, **kwargs):
    raise NotImplementedError


@create_app.register(app=BaseApp)
def create_baseapp(app, settings, scan=True, **kwargs):

    s = copy.deepcopy(default_settings)
    for k in settings.keys():
        if k in s.keys():
            for j, v in settings[k].items():
                s[k][j] = v
        else:
            s[k] = settings[k]

    settings = s

    # initialize app

    if scan:
        morepath.autoscan()
        for scanmodpath in (settings['morpfw']['scan'] or []):
            scanmod = importlib.import_module(scanmodpath)
            morepath.scan(package=scanmod)

    app_settings = settings['application']

    authnpolicy_settings = app_settings['authn_policy_settings']
    authnpol_mod, authnpol_clsname = (
        app_settings['authn_policy'].strip().split(':'))

    authnpolicy = getattr(importlib.import_module(
        authnpol_mod), authnpol_clsname)(authnpolicy_settings)

    get_identity_policy = authnpolicy.get_identity_policy
    verify_identity = authnpolicy.verify_identity

    mounted_apps = app_settings['mounted_apps']
    if getattr(authnpolicy, 'app_cls', None):
        mounted_apps.append({
            'app_cls': authnpolicy.app_cls,
            'authn_policy': app_settings['authn_policy'],
            'authn_policy_settings': app_settings['authn_policy_settings']
        })
    for iapp in mounted_apps:
        if 'app_cls' in iapp.keys():
            iapp_cls = iapp['app_cls']
        else:
            iapp_path = iapp['app']
            iapp_mod, iapp_clsname = iapp_path.strip().split(':')
            iapp_cls = getattr(importlib.import_module(iapp_mod), iapp_clsname)

        if iapp.get('authn_policy', None):
            iapp_authnpolicy_settings = iapp.get('authn_policy_settings', {})
            iapp_authnpol_mod, iapp_authnpol_clsname = (
                iapp['authn_policy'].strip().split(':'))
            iapp_authnpolicy = getattr(importlib.import_module(
                iapp_authnpol_mod), iapp_authnpol_clsname)(iapp_authnpolicy_settings)
            iapp_get_identity_policy = iapp_authnpolicy.get_identity_policy
            iapp_verify_identity = iapp_authnpolicy.verify_identity
            iapp_cls.identity_policy()(iapp_get_identity_policy)
            iapp_cls.verify_identity()(iapp_verify_identity)
            if getattr(iapp_cls, 'authn_provider', None):
                iapp_cls.authn_provider()(iapp_authnpolicy.get_app)
        else:
            iapp_cls.identity_policy()(get_identity_policy)
            iapp_cls.verify_identity()(verify_identity)
            if getattr(iapp_cls, 'authn_provider', None):
                iapp_cls.authn_provider()(authnpolicy.get_app)

        iapp_cls.init_settings(settings)
        iapp_cls._raw_settings = settings
        iapp_cls.commit()

    app.identity_policy()(get_identity_policy)
    app.verify_identity()(verify_identity)
    if authnpolicy.app_cls:
        app.authn_provider()(lambda: authnpolicy.app_cls())
    app.init_settings(settings)
    app._raw_settings = settings

    if settings['application']['development_mode']:
        os.environ['MOREPATH_TEMPLATE_AUTO_RELOAD'] = "1"

    app.commit()

    celery_settings = settings['worker']['celery_settings']
    app.celery.conf.update(**celery_settings)
    application = app()
    return application


@create_app.register(app=SQLApp)
def create_sqlapp(app, settings, scan=True, **kwargs):

    application = create_baseapp(app=app, settings=settings, scan=scan,
                                 **kwargs)

    application.initdb()
    return application


def create_admin(app: morepath.App, username: str, password: str, email: str, session=Session):
    appreq = app.request_class(app=app, environ={'PATH_INFO': '/'})
    try:
        authapp = app.get_authn_provider(appreq)
    except NotImplementedError:
        return

    request = authapp.request_class(app=authapp, environ={'PATH_INFO': '/'})

    transaction.manager.begin()
    get_authn_storage = authapp.get_storage
    usercol = UserCollection(request, get_authn_storage(UserModel, request))
    userobj = usercol.create({'username': username,
                              'password': password,
                              'email': email,
                              'state': 'active'})
    gstorage = get_authn_storage(GroupModel, request)
    group = gstorage.get('__default__')
    group.add_members([userobj.userid])
    group.grant_member_role(userobj.userid, 'administrator')
    transaction.manager.commit()
    return userobj


def run(app, settings, host='127.0.0.1', port=5000, ignore_cli=True):
    application = create_app(app, settings)
    morepath.run(application, host=host, port=port, ignore_cli=ignore_cli)


def runprod(app, settings, host='127.0.0.1', port=5000, ignore_cli=True):
    service = 'gunicorn'
    server = {'listen_address': host, 'listen_port': port}
    opts = {}
    opts['loglevel'] = server.get('log_level', 'INFO')
    opts['log_directory'] = '/tmp/applog'
    appdn = '%s:%s' % (app.__module__, app.__name__)
    os.environ['MORP_APP'] = appdn
    logconfig = '''
[loggers]
keys=root, gunicorn.error, gunicorn.access

[handlers]
keys=console, error_file, access_file, application_file

[formatters]
keys=generic, access

[logger_root]
level=%(loglevel)s
handlers=console, application_file

[logger_gunicorn.error]
level=%(loglevel)s
handlers=error_file
propagate=1
qualname=gunicorn.error

[logger_gunicorn.access]
level=%(loglevel)s
handlers=access_file
propagate=0
qualname=gunicorn.access

[handler_console]
class=StreamHandler
formatter=generic
args=(sys.stdout, )

[handler_error_file]
class=logging.FileHandler
formatter=generic
args=('%(log_directory)s/errors.log',)

[handler_access_file]
class=logging.FileHandler
formatter=access
args=('%(log_directory)s/access.log',)

[handler_application_file]
class=logging.FileHandler
formatter=generic
args=('%(log_directory)s/application.log',)


[formatter_generic]
format=%%(asctime)s [%%(process)d] [%%(levelname)s] %%(message)s
datefmt=%%Y-%%m-%%d %%H:%%M:%%S
class=logging.Formatter

[formatter_access]
format=%%(message)s
class=logging.Formatter
    ''' % opts
    workers = (multiprocessing.cpu_count() * 2) + 1
    logconf = tempfile.mktemp()
    with open(logconf, 'w') as f:
        f.write(logconfig)
    subprocess.call([
        service,
        '--log-config', logconf,
        '-b', '%(listen_address)s:%(listen_port)s' % server,
        '-k', 'eventlet',
        '--workers', str(server.get('workers', workers)),
        '--max-requests', str(server.get('max_requests', 1000)),
        '--max-requests-jitter', str(server.get('max_requests_jitter', 1000)),
        '--worker-connections', str(server.get('worker_connections', 1000)),
        '--timeout', str(server.get('worker_timeout', 30)), 'morpfw.wsgi:app'])
