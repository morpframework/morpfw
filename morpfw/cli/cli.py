import copy
import errno
import importlib
import json
import os
import sys
from random import randint

import click
import yaml

from ..main import default_settings
from .generate_config import genconfig


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
