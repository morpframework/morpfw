import argparse
import importlib
import os

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

    dburi = click.prompt(
        "Application DB URI",
        default="postgresql://postgres:postgres@localhost:5432/%s" % proj_name,
    )
    blobstorage_uri = click.prompt(
        "Blobstorage URI", default=r"fsblob://%(here)s/blobstorage"
    )
    beaker_session_type = click.prompt("Beaker Session Type", default="ext:database")
    beaker_session_uri = click.prompt(
        "Beaker Session URI",
        default="postgresql://postgres:postgres@localhost:5432/%s_cache" % proj_name,
    )
    beaker_cache_type = click.prompt("Beaker Cache Type", default=beaker_session_type)
    beaker_cache_uri = click.prompt("Beaker Cache URI", default=beaker_session_uri,)
    celery_broker_uri = click.prompt(
        "Celery Broker URI", default="amqp://guest:guest@localhost:5672/%s" % proj_name
    )
    celery_result_backend = click.prompt(
        "Celery Result Backend",
        default="db+postgresql://postgres@localhost:5432/%s_cache" % proj_name,
    )
    return {
        "fernet_key": Fernet.generate_key().decode("utf-8"),
        "dburi": dburi,
        "blobstorage_uri": blobstorage_uri,
        "beaker_session_type": beaker_session_type,
        "beaker_session_uri": beaker_session_uri,
        "beaker_cache_type": beaker_cache_type,
        "beaker_cache_uri": beaker_cache_uri,
        "celery_broker_uri": celery_broker_uri,
        "celery_result_backend": celery_result_backend,
        "app_cls": "%s:%s" % (app_cls.__module__, app_cls.__name__),
        "app_module": app_cls.__module__.split(".")[0],
        "app_title": "Application",
    }


def genconfig(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("application", help="Application class, in format module:Class")
    parser.add_argument(
        "-o", "--output", default=None, help="Output file (default to stdout)"
    )
    args = parser.parse_args(argv)

    mod_name, cls_name = args.application.split(":")
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
        print("\n\n")
        print("# ---- Generated Config ----")
        print(out)
        print("# ---- End Of Generated Config ----")
    else:
        with open(args.output) as of:
            of.write(out)
