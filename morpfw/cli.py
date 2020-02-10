import code
import copy
import getpass
import importlib
import json
import os
import readline
import rlcompleter
import socket
import sys
import threading
from datetime import datetime
from urllib.parse import urlparse

import click

import hydra
import morepath
import morpfw
import yaml

from .alembic import drop_all
from .main import create_admin, create_app, default_settings
from .util import mock_request


def load_settings(settings_file, default=default_settings):
    default_settings = os.environ.get("MORP_SETTINGS", {})
    if settings_file is None:
        settings = default_settings
    elif not os.path.exists(settings_file):
        settings = default_settings
    else:
        raw_file = open(settings_file).read()
        raw_file = raw_file.replace(r"%(here)s", os.getcwd())
        settings = yaml.load(raw_file)

    s = copy.deepcopy(default)
    for k in settings.keys():
        if k in s.keys():
            for j, v in settings[k].items():
                s[k][j] = v
        else:
            s[k] = settings[k]

    settings = s
    os.environ["MORP_SETTINGS"] = json.dumps(settings)
    return settings


def load(settings_file: str = None, host: str = None, port: int = None):
    settings = load_settings(settings_file)

    if "application" not in settings:
        print("'application' section is required in settings")
        sys.exit(1)
    if "factory" not in settings["application"]:
        print("Missing application:factory entry in settings")
        sys.exit(1)
    if "class" not in settings["application"]:
        print("Missing application:class entry in settings")
        sys.exit(1)

    if "server" in settings:
        if not host:
            host = settings["server"].get("listen_host", "127.0.0.1")
        if not port:
            port = settings["server"].get("listen_port", 5432)

    sys.path.append(os.getcwd())

    factory_path = settings["application"]["factory"]
    mod, fname = factory_path.split(":")
    factory = getattr(importlib.import_module(mod), fname)

    app_path = settings["application"]["class"]
    mod, clsname = app_path.split(":")
    app_cls = getattr(importlib.import_module(mod), clsname)
    return {
        "factory": factory,
        "class": app_cls,
        "settings": settings,
        "host": host,
        "port": port,
    }


@click.group()
@click.option("-s", "--settings", type=str, default=None, help="path to settings.yml")
@click.pass_context
def cli(ctx, settings):
    """Manage Morp application services"""
    ctx.ensure_object(dict)
    ctx.obj["settings"] = settings


@cli.command(help="start web server")
@click.option("-h", "--host", default=None, help="Host")
@click.option("-p", "--port", default=None, type=int, help="Port")
@click.option("--prod", default=False, type=bool, is_flag=True, help="Production mode")
@click.pass_context
def start(ctx, host, port, prod):
    param = load(ctx.obj["settings"], host, port)
    if prod:
        morpfw.runprod(
            param["factory"](param["settings"]),
            settings=param["settings"],
            host=param["host"],
            port=param["port"],
            ignore_cli=True,
        )
    else:
        morpfw.run(
            param["factory"](param["settings"]),
            settings=param["settings"],
            host=param["host"],
            port=param["port"],
            ignore_cli=True,
        )


@cli.command(help="start celery worker")
@click.pass_context
def solo_worker(ctx):
    print(threading.get_ident())
    param = load(ctx.obj["settings"])
    hostname = socket.gethostname()
    ws = param["settings"]["configuration"]["morpfw.celery"]
    now = datetime.utcnow().strftime(r"%Y%m%d%H%M")
    param["factory"](param["settings"], instantiate=False)
    worker = param["class"].celery.Worker(
        hostname="worker%s.%s" % (now, hostname), **ws
    )
    worker.start()


@cli.command(help="start celery beat scheduler")
@click.pass_context
def scheduler(ctx):
    param = load(ctx.obj["settings"])
    hostname = socket.gethostname()
    ss = param["settings"]["configuration"]["morpfw.celery"]
    sched = param["class"].celery.Beat(hostname="scheduler.%s" % hostname, **ss)
    sched.run()


@cli.command(help="register administrator user (only for app using PAS)")
@click.option("-u", "--username", required=True, help="Username", prompt=True)
@click.option("-e", "--email", required=True, help="Email address", prompt=True)
@click.option(
    "-p",
    "--password",
    required=True,
    help="Password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
)
@click.pass_context
def register_admin(ctx, username, email, password):
    param = load(ctx.obj["settings"])
    app = param["factory"](param["settings"])
    while not isinstance(app, morepath.App):
        wrapped = getattr(app, "app", None)
        if wrapped:
            app = wrapped
        else:
            raise ValueError("Unable to locate app object from middleware")
    user = create_admin(app=app, username=username, password=password, email=email)
    if user is None:
        print("Application is not using Pluggable Auth Service")


@cli.command(help="Start MorpFW shell")
@click.pass_context
def shell(ctx):
    from morepath.authentication import Identity

    param = load(ctx.obj["settings"])
    app = param["factory"](param["settings"])

    while not isinstance(app, morepath.App):
        wrapped = getattr(app, "app", None)
        if wrapped:
            app = wrapped
        else:
            raise ValueError("Unable to locate app object from middleware")

    settings = param["settings"]

    server_url = settings.get("server", {}).get("server_url", "http://localhost")
    parsed = urlparse(server_url)
    environ = {
        "PATH_INFO": "/",
        "wsgi.url_scheme": parsed.scheme,
        "SERVER_PROTOCOL": "HTTP/1.1",
        "HTTP_HOST": parsed.netloc,
    }
    request = app.request_class(app=app, environ=environ)
    session = request.db_session
    _shell(
        {
            "session": session,
            "request": request,
            "app": app,
            "settings": settings,
            "Identity": Identity,
        }
    )


def _shell(vars):

    # do something here

    readline.set_completer(rlcompleter.Completer(vars).complete)
    readline.parse_and_bind("tab: complete")
    shell = code.InteractiveConsole(vars)
    shell.interact()


@cli.command(help="Reset database")
@click.pass_context
def resetdb(ctx):
    param = load(ctx.obj["settings"])
    app = param["factory"](param["settings"])

    while not isinstance(app, morepath.App):
        wrapped = getattr(app, "app", None)
        if wrapped:
            app = wrapped
        else:
            raise ValueError("Unable to locate app object from middleware")

    settings = param["settings"]

    request = mock_request(app, settings)

    drop_all(request)


if __name__ == "__main__":
    cli()
