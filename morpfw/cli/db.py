import copy
import importlib
import os
import sys
import tempfile
from configparser import RawConfigParser

import click
import morpfw
import reg
from alembic.config import CommandLine as AlembicCLI
from alembic.config import Config as AlembicCfg
from alembic.config import main as alembic_main

from ..alembic import drop_all
from .cli import cli, confirmation_dialog, load


@reg.dispatch(reg.match_class("app", lambda app_cls, settings: app_cls))
def alembic_config(app_cls, settings: dict):
    raise NotImplementedError("alembic_config for %s" % app_cls)


@reg.dispatch(reg.match_class("app", lambda app_cls, settings: app_cls))
def alembic_logging_config(app_cls, settings: dict) -> dict:
    raise NotImplementedError("alembic_logging_config %s" % app_cls)


@alembic_logging_config.register(app=morpfw.BaseApp)
def default_alembic_logging_config(app_cls, settings: dict):
    return {
        "loggers": {"keys": "root,sqlalchemy,alembic"},
        "handlers": {"keys": "console"},
        "formatters": {"keys": "generic",},
        "logger_root": {"level": "WARN", "handlers": "console", "qualname": None},
        "logger_sqlalchemy": {
            "level": "WARN",
            "handlers": None,
            "qualname": "sqlalchemy.engine",
        },
        "logger_alembic": {"level": "INFO", "handlers": None, "qualname": "alembic"},
        "handler_console": {
            "class": "StreamHandler",
            "args": "(sys.stderr,)",
            "level": "NOTSET",
            "formatter": "generic",
        },
        "formatter_generic": {
            "format": r"%(levelname)-5.5s [%(name)s] %(message)s",
            "datefmt": r"%H:%M:%S",
        },
    }


@alembic_config.register(app=morpfw.BaseApp)
def default_alembic_config(app_cls, settings: dict) -> AlembicCfg:
    config = settings["configuration"]
    proj = "default"
    acfg = AlembicCfg()
    script_location = config.get(
        "alembic.migration_script_location", os.path.join(os.getcwd(), "migrations")
    )
    acfg.set_main_option("script_location", script_location)
    acfg.set_main_option("databases", proj)
    acfg.set_section_option(
        proj, "sqlalchemy.url", config["morpfw.storage.sqlstorage.dburi"]
    )
    logging_cfg = alembic_logging_config(app_cls, settings)

    log_cfg = RawConfigParser()
    for section, opts in logging_cfg.items():
        for k, v in opts.items():
            v = str(v) if v is not None else ""
            log_cfg.setdefault(section, {})
            log_cfg[section][k] = v

    cfg_tmp = tempfile.mktemp(prefix="mfw-logging", suffix=".ini")
    with open(cfg_tmp, "w") as f:
        log_cfg.write(f)

    acfg.logging_config_file_name = cfg_tmp
    return acfg


@cli.command(help="Reset database")
@click.pass_context
def resetdb(ctx):
    param = load(ctx.obj["settings"])

    settings = param["settings"]

    if not confirmation_dialog():
        return

    with morpfw.request_factory(settings) as request:
        drop_all(request)


@cli.command(help="Vacuum database")
@click.pass_context
def vacuum(ctx):
    param = load(ctx.obj["settings"])

    settings = param["settings"]

    with morpfw.request_factory(settings) as request:

        types = request.app.config.type_registry.get_typeinfos(request)
        for typeinfo in types.values():

            collection = request.get_collection(typeinfo["name"])
            vacuum_f = getattr(collection.storage, "vacuum", None)
            if vacuum_f:
                print("Vacuuming %s" % typeinfo["name"])
                items = vacuum_f()
                print("%s record(s) affected" % items)


@cli.command(
    help="manage alembic migration",
    context_settings=dict(ignore_unknown_options=True, allow_extra_args=True),
)
@click.pass_context
def db(ctx):
    param = load(ctx.obj["settings"])
    settings = param["settings"]

    modname, cname = settings["application"]["class"].split(":")
    mod = importlib.import_module(modname)
    app_cls = getattr(mod, cname)

    acfg = alembic_config(app_cls, settings)

    argv = copy.copy(sys.argv)
    if "-s" in argv:
        sindex = argv.index("-s")
        argv = argv[:sindex] + argv[sindex + 2 :]
    if "--settings" in argv:
        sindex = argv.index("--settings")
        argv = argv[:sindex] + argv[sindex + 2 :]

    prog = "%s %s" % (argv[0], argv[1])
    acli = AlembicCLI(prog=prog)
    options = acli.parser.parse_args(argv[2:])
    acli.run_cmd(acfg, options)
