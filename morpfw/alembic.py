import os
import sys

from sqlalchemy import MetaData, create_engine
from sqlalchemy import inspect as Inspector
from sqlalchemy.schema import DropSchema

from alembic import command
from alembic.config import Config


def _load_engines(config):
    engines = {}
    for k, v in config.items():
        k = k.strip()
        prefix = "morpfw.storage.sqlstorage.dburl"
        if k.startswith(prefix):
            name = k.replace(prefix, "").strip()
            if name == "":
                name = "default"
            elif name.startswith("."):
                name = name[1:]

            engines[name] = {"dburl": v}
    return engines


def drop_all(request):

    config = request.app.settings.configuration.__dict__
    engines = _load_engines(config)

    for n, conf in engines.items():
        param = dict([(k, v) for k, v in conf.items() if k != "dburl"])
        engine = create_engine(conf["dburl"], **param)
        inspect = Inspector(engine)
        print("Clearing engine: %s" % n)
        for schema in inspect.get_schema_names():
            if schema in ["information_schema"]:
                continue
            if schema.startswith("pg_"):
                continue
            meta = MetaData(engine, schema=schema)
            print(".. Clearing tables from schema {}".format(schema))
            meta.reflect()
            meta.drop_all()
            if schema in ["public", "dbo"]:
                continue

            print("Dropping schema {}".format(schema))
            engine.execute(DropSchema(schema))
        print("Done")
