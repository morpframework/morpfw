import argparse
import importlib
import os
import sys

import click
import morpfw
import reg
from cryptography.fernet import Fernet
from jinja2 import Template


@reg.dispatch(reg.match_class("app", lambda app_cls: app_cls))
def get_settings_opts(app_cls):
    raise NotImplementedError()


@get_settings_opts.register(app=morpfw.BaseApp)
def default_get_settings_opts(app_cls):
    proj_name = app_cls.__module__.split(".")[0]

    dburl = click.prompt(
        "Application DB URL",
        default="postgresql://postgres:postgres@localhost:5432/%s" % proj_name,
    )
    blobstorage_url = click.prompt(
        "Blobstorage URL", default=r"fsblob://%(here)s/blobstorage"
    )
    beaker_session_type = click.prompt("Beaker Session Type", default="ext:database")
    beaker_session_url = click.prompt(
        "Beaker Session URL",
        default="postgresql://postgres:postgres@localhost:5432/%s_cache" % proj_name,
    )
    beaker_cache_type = click.prompt("Beaker Cache Type", default=beaker_session_type)
    beaker_cache_url = click.prompt("Beaker Cache URL", default=beaker_session_url,)
    celery_broker_url = click.prompt(
        "Celery Broker URL", default="amqp://guest:guest@localhost:5672/%s" % proj_name
    )
    celery_result_backend = click.prompt(
        "Celery Result Backend",
        default="db+postgresql://postgres@localhost:5432/%s_cache" % proj_name,
    )
    return {
        "fernet_key": Fernet.generate_key().decode("utf-8"),
        "dburl": dburl,
        "blobstorage_url": blobstorage_url,
        "beaker_session_type": beaker_session_type,
        "beaker_session_url": beaker_session_url,
        "beaker_cache_type": beaker_cache_type,
        "beaker_cache_url": beaker_cache_url,
        "celery_broker_url": celery_broker_url,
        "celery_result_backend": celery_result_backend,
        "app_cls": "%s:%s" % (app_cls.__module__, app_cls.__name__),
        "app_module": app_cls.__module__.split(".")[0],
        "app_title": "Application",
    }


def genconfig(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--application",
        default=None,
        help="Application class, in format module:Class",
    )
    parser.add_argument("-o", "--output", default=None, help="Output file")
    args = parser.parse_args(argv)

    if args.application is None:
        if "MFW_APP" in os.environ:
            application = os.environ["MFW_APP"]
        else:
            parser.error("Application argument is required")
    else:
        application = args.application

    mod_name, cls_name = application.split(":")
    mod = importlib.import_module(mod_name)
    app_cls = getattr(mod, cls_name)

    for ac in app_cls.__mro__:
        c_mod = importlib.import_module(ac.__module__)
        mod_dir = os.path.dirname(c_mod.__file__)
        tmpl = os.path.join(mod_dir, "settings.yml.tmpl")

        if os.path.exists(tmpl):
            with open(tmpl, "r") as f:
                tmpl_str = f.read()

            template = Template(tmpl_str)
            out = template.render(get_settings_opts(app_cls))
            break

    if args.output is None:
        home_env = app_cls.home_env
        if home_env in os.environ:
            output = os.path.join(os.environ[home_env], "settings.yml")
        else:
            print("%s is not set. Using current directory" % home_env, file=sys.stderr)
            output = "settings.yml"
    else:
        output = args.output

    if os.path.exists(output):
        print("%s already exist" % output, file=sys.stderr)
        sys.exit(1)

    with open(output, "w") as of:
        of.write(out)

    print("Written %s" % output)
