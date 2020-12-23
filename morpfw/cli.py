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
import runpy
import socket
import sys
import threading
import time
from datetime import datetime
from random import randint
from urllib.parse import urlparse

import click
import morepath
import morpfw
import rulez
import transaction
import yaml
from alembic.config import main as alembic_main

from .alembic import drop_all
from .main import create_admin, default_settings
from .request import request_factory


def load_settings(settings_file, default=default_settings):
    dsettings = os.environ.get("MORP_SETTINGS", {})
    if settings_file is None:
        settings = dsettings
    elif not os.path.exists(settings_file):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), settings_file)
    else:
        raw_file = open(settings_file).read()
        raw_file = raw_file.replace(r"%(here)s", os.getcwd())
        settings = yaml.load(raw_file, Loader=yaml.Loader)

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


def confirmation_dialog(message="Are you sure you want to proceed?", token_length=6):

    token = ""
    for i in range(token_length):
        x = randint(0, 9)
        token += str(x)

    ans = input("%s \n(Please enter '%s' to confirm): " % (message, token))
    if ans.strip() != token:
        print("Invalid confirmation token")
        return False
    return True


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


@cli.command(help="alias to 'worker'")
@click.pass_context
def solo_worker(ctx):
    return start_worker(ctx)


@cli.command(help="start celery worker")
@click.pass_context
def worker(ctx):
    return start_worker(ctx)


def start_worker(ctx):
    print(threading.get_ident())
    param = load(ctx.obj["settings"])
    hostname = socket.gethostname()
    ws = param["settings"]["configuration"]["morpfw.celery"]
    now = datetime.utcnow().strftime(r"%Y%m%d%H%M")
    # scan
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
    # scan
    param["factory"](param["settings"], instantiate=False)
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
    settings = param["settings"]
    with request_factory(settings, extra_environ={"morpfw.nomemoize": True}) as request:
        user = create_admin(request, username=username, password=password, email=email)
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
    starttime = time.time()
    prof.enable()
    _start_shell(ctx, script, spawn_shell=False)
    prof.disable()
    endtime = time.time()
    print(f"Time taken: {endtime - starttime:.3f} seconds")
    outfile = script + ".pstats"
    if os.path.exists(outfile):
        os.unlink(outfile)
    prof.dump_stats(outfile)
    print(f"Profiler result stored as {outfile}")


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
    starttime = time.time()
    _start_shell(ctx, script, spawn_shell=False)
    if commit:
        transaction.commit()
    endtime = time.time()
    print(f"Time taken: {endtime - starttime:.3f} seconds")


def _start_shell(ctx, script, spawn_shell=True):
    from morepath.authentication import Identity

    param = load(ctx.obj["settings"])
    settings = param["settings"]
    request = request_factory(settings)
    session = request.db_session

    def commit():
        transaction.commit()
        sys.exit()

    localvars = {
        "session": session,
        "request": request,
        "app": request.app,
        "settings": settings,
        "Identity": Identity,
        "commit": commit,
        "morpfw": morpfw,
        "rulez": rulez,
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
    banner = "\nMorpFW Interactive Console\nAvailable globals : %s\n" % (
        ", ".join(vars.keys())
    )
    shell = code.InteractiveConsole(vars)
    shell.interact(banner=banner)


@cli.command(help="Reset database")
@click.pass_context
def resetdb(ctx):
    param = load(ctx.obj["settings"])

    settings = param["settings"]

    if not confirmation_dialog():
        return

    with request_factory(settings) as request:
        drop_all(request)


@cli.command(help="Vacuum database")
@click.pass_context
def vacuum(ctx):
    param = load(ctx.obj["settings"])

    settings = param["settings"]

    with request_factory(settings) as request:

        types = request.app.config.type_registry.get_typeinfos(request)
        for typeinfo in types.values():

            collection = request.get_collection(typeinfo["name"])
            vacuum_f = getattr(collection.storage, "vacuum", None)
            if vacuum_f:
                print("Vacuuming %s" % typeinfo["name"])
                items = vacuum_f()
                print("%s record(s) affected" % items)


@cli.command(help="manage alembic migration")
@click.pass_context
def migration(ctx, options):
    pass


@cli.command(help="Update elasticsearch indexes")
@click.pass_context
def update_esindex(ctx):
    param = load(ctx.obj["settings"])

    settings = param["settings"]

    with request_factory(settings) as request:

        types = request.app.config.type_registry.get_typeinfos(request)
        for typeinfo in types.values():
            collection = request.get_collection(typeinfo["name"])
            storage = collection.storage
            if isinstance(storage, morpfw.ElasticSearchStorage):
                print("Creating index %s .. " % storage.index_name, end="")
                if storage.create_index(collection):
                    print("OK")
                else:
                    if storage.update_index(collection):
                        print("UPDATED")
                    else:
                        raise AssertionError("Unknown error")


@cli.command(help="delete all elasticsearch indexes")
@click.pass_context
def reset_esindex(ctx):

    if not confirmation_dialog():
        return

    param = load(ctx.obj["settings"])

    settings = param["settings"]

    with request_factory(settings) as request:

        types = request.app.config.type_registry.get_typeinfos(request)
        client = request.get_es_client()
        for typeinfo in types.values():
            collection = request.get_collection(typeinfo["name"])
            storage = collection.storage
            if isinstance(storage, morpfw.ElasticSearchStorage):
                print("Deleting index %s .. " % storage.index_name, end="")
                client.indices.delete(storage.index_name)
                print("OK")


def main():
    if "migration" in sys.argv:
        argv = sys.argv[sys.argv.index("migration") + 1 :]
        sys.exit(alembic_main(argv, "morpfw migration"))
    else:
        cli()


def run_module(argv=sys.argv):
    if len(argv) <= 1:
        print("Usage: %s [module]" % argv[0])
        sys.exit(1)
    mod = argv[1]
    sys.argv = argv[0:1] + argv[2:]
    runpy.run_module(mod, run_name="__main__", alter_sys=True)


def run_module_profile(argv=sys.argv):
    mod = argv[1]
    sys.argv = argv[0:1] + argv[2:]
    prof = cProfile.Profile()
    starttime = time.time()
    prof.enable()
    runpy.run_module(mod, run_name="__main__", alter_sys=True)
    prof.disable()
    endtime = time.time()
    print(f"Time taken: {endtime - starttime:.3f} seconds")
    outfile = mod + ".pstats"
    if os.path.exists(outfile):
        os.unlink(outfile)
    prof.dump_stats(outfile)
    print(f"Profiler result stored as {outfile}")


if __name__ == "__main__":
    main()
