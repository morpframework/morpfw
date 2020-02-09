import os

from sqlalchemy import MetaData, create_engine

from alembic import command
from alembic.config import Config


def _load_engines(config):
    engines = {}
    for k, v in config.items():
        k = k.strip()
        prefix = "morpfw.storage.sqlstorage.dburi"
        if k.startswith(prefix):
            name = k.replace(prefix, "").strip()
            if name == "":
                name = "default"
            elif name.startswith("."):
                name = name[1:]

            engines[name] = {"dburi": v}
    return engines


def migrate(request):
    config = request.app.settings.configuration.__dict__
    engines = _load_engines(config)

    for path in request.app.__class__.all_migration_scripts():
        cfg = Config(os.path.join(path, "alembic.ini"))
        cfg.set_main_option("databases", ", ".join(engines.keys()))
        cfg.set_main_option("script_location", path)
        for e, es in engines.items():
            cfg.set_section_option(e, "sqlalchemy.url", es["dburi"])

        command.upgrade(cfg, "head")


def drop_all(request):

    config = request.app.settings.configuration.__dict__
    engines = _load_engines(config)

    for n, conf in engines.items():
        param = dict([(k, v) for k, v in conf.items() if k != "dburi"])
        engine = create_engine(conf["dburi"], **param)
        meta = MetaData(engine)
        meta.reflect()
        meta.drop_all()
