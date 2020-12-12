import copy
import importlib
import multiprocessing
import os
import subprocess
import tempfile

import morepath
import reg
import sqlalchemy
import transaction
import yaml
from beaker.middleware import CacheMiddleware as BeakerCacheMiddleware
from beaker.middleware import SessionMiddleware as BeakerMiddleware
from celery import Celery
from more.basicauth import BasicAuthIdentityPolicy
from zope.sqlalchemy import register as register_session

from .app import BaseApp, SQLApp
from .authn.pas.group.model import GroupModel, GroupSchema
from .authn.pas.group.path import get_group_collection
from .authn.pas.user.model import UserCollection, UserModel, UserSchema
from .authn.pas.user.path import get_user_collection
from .exc import ConfigurationError
from .request import Request, default_settings, request_factory
from .sql import Base


def create_app(settings, scan=True, **kwargs):
    assert "class" in settings["application"]
    app_mod, app_clsname = settings["application"]["class"].split(":")
    app = getattr(importlib.import_module(app_mod), app_clsname)

    s = copy.deepcopy(default_settings)
    for k in settings.keys():
        if k in s.keys():
            for j, v in settings[k].items():
                s[k][j] = v
        else:
            s[k] = settings[k]

    settings = s

    # initialize app
    config = settings["configuration"]

    if scan:
        morepath.autoscan()
        for scanmodpath in config["morpfw.scan"] or []:
            scanmod = importlib.import_module(scanmodpath)
            morepath.scan(package=scanmod)

    authnpolicy_settings = config["morpfw.authn.policy.settings"]
    authnpol_mod, authnpol_clsname = config["morpfw.authn.policy"].strip().split(":")

    authnpolicy = getattr(importlib.import_module(authnpol_mod), authnpol_clsname)(
        authnpolicy_settings
    )

    get_identity_policy = authnpolicy.get_identity_policy
    verify_identity = authnpolicy.verify_identity

    app.identity_policy()(get_identity_policy)
    app.verify_identity()(verify_identity)
    app.init_settings(settings)
    app._raw_settings = settings

    if config["app.development_mode"]:
        os.environ["MOREPATH_TEMPLATE_AUTO_RELOAD"] = "1"

    if not app.is_committed():
        app.commit()

    celery_settings = config["morpfw.celery"]
    app.celery.conf.update(**celery_settings)
    application = app()

    # wrap with beaker session and cache manager

    beaker_settings = {}

    for k, v in settings["configuration"].items():
        if k.startswith("morpfw.beaker."):
            keylen = len("morpfw.beaker.")
            beaker_settings[k[keylen:]] = v

    if "session.type" in beaker_settings:
        application = BeakerMiddleware(application, beaker_settings)
    if "cache.type" in beaker_settings:
        application = BeakerCacheMiddleware(application, beaker_settings)
    return application


def create_admin(request: Request, username: str, password: str, email: str):
    transaction.manager.begin()
    usercol = get_user_collection(request)
    userobj = usercol.create(
        {
            "username": username,
            "password": password,
            "email": email,
            "state": "active",
            "source": "local",
            "is_administrator": True,
            "timezone": "UTC",
        }
    )
    gcol = request.get_collection("morpfw.pas.group")
    group = gcol.get_by_groupname("__default__")
    group.add_members([userobj.userid])
    group.grant_member_role(userobj.userid, "administrator")
    transaction.manager.commit()
    return userobj


def run(app, settings, host="127.0.0.1", port=5000, ignore_cli=True):
    morepath.run(app, host=host, port=port, ignore_cli=ignore_cli)


def runprod(app, settings, host="127.0.0.1", port=5000, ignore_cli=True, workers=None):
    service = "gunicorn"
    server_listen = {"listen_address": host, "listen_port": port}
    server = settings["server"].copy()
    server.update(server_listen)
    opts = {}
    opts["loglevel"] = server.get("log_level", "INFO")
    opts["log_directory"] = settings.get("logging", {}).get("log_directory", "/tmp")
    os.environ["MORP_APP_FACTORY"] = settings["application"]["factory"]
    logconfig = (
        """
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
    """
        % opts
    )
    if workers is None:
        workers = (multiprocessing.cpu_count() * 2) + 1

    logconf = tempfile.mktemp()
    with open(logconf, "w") as f:
        f.write(logconfig)

    opts = [
        "--log-config",
        logconf,
        "-b",
        "%(listen_address)s:%(listen_port)s" % server,
        "--workers",
        str(server.get("workers", workers)),
        "--max-requests",
        str(server.get("max_requests", 1000)),
        "--max-requests-jitter",
        str(server.get("max_requests_jitter", 1000)),
        "--worker-connections",
        str(server.get("worker_connections", 1000)),
        "--timeout",
        str(server.get("worker_timeout", 30)),
    ]

    subprocess.call([service] + opts + ["morpfw.wsgi:app"])


def set_buildout_environ(config: str) -> None:
    envs = {}
    for l in config.strip().split("\n"):
        sep = l.find(":")
        if sep < 0:
            raise ValueError(l)
        k = l[:sep].strip()
        v = l[sep + 1 :].strip()
        envs[k] = v

    for k, v in envs.items():
        os.environ[k] = v

    if "BUILDOUT_BINDIR" in envs.keys():
        bindir = envs["BUILDOUT_BINDIR"]
        os.environ["PATH"] = "%s:%s" % (bindir, os.environ["PATH"])

