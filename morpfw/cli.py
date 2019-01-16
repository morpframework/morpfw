from argh import arg, dispatch_commands
import importlib
import os
import sys
from .main import create_app
from .main import create_admin
import morepath
import yaml
import morpfw
import getpass
import socket
from datetime import datetime


def load(app_path, settings_file, host=None, port=None):
    settings = yaml.load(open(settings_file))

    if not app_path:
        if 'application' not in settings:
            print("'application' section is required in settings")
            sys.exit(1)
        if 'app' not in settings['application']:
            print("Missing application:app entry in settings")
        app_path = settings['application']['app']

    if 'server' in settings:
        if not host:
            host = settings['server'].get('listen_host', '127.0.0.1')
        if not port:
            port = settings['server'].get('listen_port', 5432)

    sys.path.append(os.getcwd())
    mod, clsname = app_path.split(':')
    app_cls = getattr(importlib.import_module(mod), clsname)

    return {
        'app_cls': app_cls,
        'settings': settings,
        'host': host,
        'port': port
    }


@arg('-a', '--app', required=False, default=None, help='Path to App class')
@arg('-s', '--settings', required=True, help='Path to settings.yml')
@arg('-h', '--host', default=None, help='Host')
@arg('-p', '--port', default=None, type=int, help='Port')
def start(app=None, settings=None, host=None, port=None):
    param = load(app, settings, host, port)
    morpfw.run(param['app_cls'], settings=param['settings'], host=param['host'],
               port=param['port'], ignore_cli=True)


@arg('-a', '--app', required=False, help='Path to App class')
@arg('-s', '--settings', required=True, help='Path to settings.yml')
def solo_worker(app=None, settings=None):
    param = load(app, settings)
    hostname = socket.gethostname()
    ws = param['settings']['worker']['celery_worker_settings']
    now = datetime.utcnow().strftime(r'%Y%m%d%H%M')
    worker = param['app_cls'].celery.Worker(
        hostname='worker%s.%s' % (now, hostname), **ws)
    worker.start()


@arg('-a', '--app', required=False, help='Path to App class')
@arg('-s', '--settings', required=True, help='Path to settings.yml')
def scheduler(app=None, settings=None):
    param = load(app, settings)
    hostname = socket.gethostname()
    ss = param['settings']['worker']['celery_scheduler_settings']
    sched = param['app_cls'].celery.Beat(
        hostname='scheduler.%s' % hostname, **ss)
    sched.start()


@arg('-a', '--app', required=False, help='Path to App class')
@arg('-s', '--settings', required=True, help='Path to settings.yml')
@arg('-u', '--username', required=True, help='Username')
@arg('-e', '--email', required=True, help='Email address')
def register_admin(app=None, settings=None, username=None, email=None):
    param = load(app, settings)
    password = getpass.getpass('Enter password for %s: ' % username)
    app = create_app(param['app_cls'], param['settings'])
    while not isinstance(app, morepath.App):
        wrapped = getattr(app, 'app', None)
        if wrapped:
            app = wrapped
        else:
            raise ValueError(
                'Unable to locate app object from middleware')
    create_admin(app=app, username=username,
                 password=password, email=email)


def run():
    dispatch_commands([start, solo_worker, register_admin, scheduler])
