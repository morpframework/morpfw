import code
import copy
import cProfile
import errno
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
import transaction
import yaml
from alembic.config import main as alembic_main

from .alembic import drop_all
from .main import create_admin, create_app, default_settings
from .util import mock_request


def load_settings(settings_file, default=default_settings):
    default_settings = os.environ.get("MORP_SETTINGS", {})
    if settings_file is None:
        settings = default_settings
    elif not os.path.exists(settings_file):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), settings_file)
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
@click.option(
    "--workers", default=None, type=int, help="Number of workers to run in  prod mode"
)
@click.pass_context
def start(ctx, host, port, prod, workers):
    param = load(ctx.obj["settings"], host, port)
    if prod:
        morpfw.runprod(
            param["factory"](param["settings"]),
            settings=param["settings"],
            host=param["host"],
            port=param["port"],
            ignore_cli=True,
            workers=workers,
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
@click.option(
    "-e", "--script", required=False, help="Script to run before spawning shell"
)
@click.pass_context
def shell(ctx, script):
    return _start_shell(ctx, script)


@cli.command(help="Profile script")
@click.option("-e", "--script", required=False, help="Script to profile")
@click.pass_context
def profile(ctx, script):
    prof = cProfile.Profile()
    prof.enable()
    _start_shell(ctx, script, spawn_shell=False)
    prof.disable()
    outfile = script + ".pstats"
    if os.path.exists(outfile):
        os.unlink(outfile)
    prof.dump_stats(script + ".pstats")


@cli.command(help="Execute script")
@click.option("-e", "--script", required=False, help="Script to run")
@click.option(
    "--commit",
    default=False,
    required=False,
    type=bool,
    is_flag=True,
    help="Commit transaction",
)
@click.pass_context
def execute(ctx, script, commit):
    _start_shell(ctx, script, spawn_shell=False)
    if commit:
        transaction.commit()


def _start_shell(ctx, script, spawn_shell=True):
    from morepath.authentication import Identity

    param = load(ctx.obj["settings"])
    settings = param["settings"]

    def fake_write(chunk):
        pass

    def start_response(*args):
        return fake_write

    server_url = settings.get("server", {}).get("server_url", "http://localhost")
    parsed = urlparse(server_url)
    environ = {
        "PATH_INFO": "/",
        "wsgi.url_scheme": parsed.scheme,
        "SERVER_PROTOCOL": "HTTP/1.1",
        "HTTP_HOST": parsed.netloc,
        "REQUEST_METHOD": "GET",
    }

    app = param["factory"](param["settings"])

    app(environ, start_response)
    while not isinstance(app, morepath.App):
        wrapped = getattr(app, "app", None)
        if wrapped:
            app = wrapped
        else:
            raise ValueError("Unable to locate app object from middleware")

    request = app.request_class(app=app, environ=environ)
    session = request.db_session
    localvars = {
        "session": session,
        "request": request,
        "app": app,
        "settings": settings,
        "Identity": Identity,
    }
    if script:
        with open(script) as f:
            src = f.read()
            glob = globals().copy()
            filepath = os.path.abspath(script)
            sys.path.insert(0, os.path.dirname(filepath))
            glob["__file__"] = filepath
            bytecode = compile(src, filepath, "exec")
            exec(bytecode, glob, localvars)
    if spawn_shell:
        _shell(localvars)


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


@cli.command(help="manage alembic migration")
@click.pass_context
def migration(ctx, options):
    pass


def main():
    if "migration" in sys.argv:
        argv = sys.argv[sys.argv.index("migration") + 1 :]
        sys.exit(alembic_main(argv, "morpfw migration"))
    else:
        cli()


if __name__ == "__main__":
    main()
