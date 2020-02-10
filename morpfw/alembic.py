import os
import sys

from alembic import command
from alembic.config import Config
from sqlalchemy import MetaData, create_engine


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


def drop_all(request):

    config = request.app.settings.configuration.__dict__
    engines = _load_engines(config)

    for n, conf in engines.items():
        param = dict([(k, v) for k, v in conf.items() if k != "dburi"])
        engine = create_engine(conf["dburi"], **param)
        meta = MetaData(engine)
        meta.reflect()
        meta.drop_all()
