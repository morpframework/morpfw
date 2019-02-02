import importlib
import os
import sys
import copy
from .main import create_app
from .main import create_admin
import morepath
import yaml
import morpfw
import getpass
import socket
import json
from datetime import datetime
from .main import default_settings
import click


def load(app_path, settings_file=None, host=None, port=None):
    if settings_file is None:
        settings = {}
    else:
        raw_file = open(settings_file).read()
        raw_file = raw_file.replace(r'%(here)s', os.getcwd())
        settings = yaml.load(raw_file)

    s = copy.deepcopy(default_settings)
    for k in settings.keys():
        if k in s.keys():
            for j, v in settings[k].items():
                s[k][j] = v
        else:
            s[k] = settings[k]

    settings = s

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
    os.environ['MORP_SETTINGS'] = json.dumps(settings)
    return {
        'app_cls': app_cls,
        'settings': settings,
        'host': host,
        'port': port
    }


@click.group()
@click.option('-s', '--settings', type=str, default=None, help='path to settings.yml')
@click.option('-a', '--app', type=str, default=None,
              help='path to App class (eg: myapp.app:App)')
@click.pass_context
def cli(ctx, settings, app):
    if app is None and settings is None:
        print('Either --app or --settings must be supplied')
    ctx.ensure_object(dict)
    ctx.obj['app'] = app
    ctx.obj['settings'] = settings


@cli.command(help='start web server')
@click.option('-h', '--host', default=None, help='Host')
@click.option('-p', '--port', default=None, type=int, help='Port')
@click.pass_context
def start(ctx, host, port):
    param = load(ctx.obj['app'], ctx.obj['settings'], host, port)
    morpfw.run(param['app_cls'], settings=param['settings'], host=param['host'],
               port=param['port'], ignore_cli=True)


@cli.command(help='start celery worker')
@click.pass_context
def solo_worker(ctx):
    param = load(ctx.obj['app'], ctx.obj['settings'])
    hostname = socket.gethostname()
    ws = param['settings']['worker']['celery_settings']
    now = datetime.utcnow().strftime(r'%Y%m%d%H%M')
    app = create_app(param['app_cls'], param['settings'])
    worker = param['app_cls'].celery.Worker(
        hostname='worker%s.%s' % (now, hostname), **ws)
    worker.start()


@cli.command(help='start celery beat scheduler')
@click.pass_context
def scheduler(ctx):
    param = load(ctx.obj['app'], ctx.obj['settings'])
    hostname = socket.gethostname()
    ss = param['settings']['worker']['celery_settings']
    app = create_app(param['app_cls'], param['settings'])
    sched = param['app_cls'].celery.Beat(
        hostname='scheduler.%s' % hostname, **ss)
    sched.run()


@cli.command(help='register administrator user (only for app using PAS)')
@click.option('-u', '--username', required=True, help='Username', prompt=True)
@click.option('-e', '--email', required=True, help='Email address', prompt=True)
@click.option('-p', '--password', required=True, help='Password', prompt=True,
              hide_input=True, confirmation_prompt=True)
@click.pass_context
def register_admin(ctx, username, email, password):
    param = load(ctx.obj['app'], ctx.obj['settings'])
    app = create_app(param['app_cls'], param['settings'])
    while not isinstance(app, morepath.App):
        wrapped = getattr(app, 'app', None)
        if wrapped:
            app = wrapped
        else:
            raise ValueError(
                'Unable to locate app object from middleware')
    user = create_admin(app=app, username=username,
                        password=password, email=email)
    if user is None:
        print('Application is not using Pluggable Auth Service')


def run():
    cli()
