from argh import arg, dispatch_commands
import importlib
import os
import sys
from .main import create_app
import morepath
import yaml
import morpfw


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
            host = settings['server'].get('listen_host', host)
        if not port:
            port = settings['server'].get('listen_port', port)

    sys.path.append(os.getcwd())
    mod, clsname = app_path.split(':')
    app_cls = getattr(importlib.import_module(mod), clsname)

    appobj = create_app(app_cls, settings)

    return {
        'app_cls': app_cls,
        'app': appobj,
        'settings': settings,
        'host': host,
        'port': port
    }


@arg('-a', '--app', required=False, default=None, help='Path to App class')
@arg('-s', '--settings', required=True, help='Path to settings.yml')
@arg('-h', '--host', default='127.0.0.1', help='Host')
@arg('-p', '--port', default=5432, type=int, help='Port')
def start(app=None, settings=None, host=None, port=None):
    param = load(app, settings, host, port)
    morpfw.run(param['app'], host=param['host'],
               port=param['port'], ignore_cli=True)


@arg('-a', '--app', required=False, help='Path to App class')
@arg('-s', '--settings', required=True, help='Path to settings.yml')
def solo_worker(app=None, settings=None, host=None, port=None):
    param = load(app, settings, host, port)
    worker = param['app_cls'].celery.Worker()
    worker.start()


def run():
    dispatch_commands([start, solo_worker])
