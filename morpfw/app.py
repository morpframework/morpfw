import os
import re
import sys
import time
import warnings
from typing import Any, Dict, List, Optional

import dectate
import morepath
import reg
import sqlalchemy
import sqlalchemy.orm
import transaction
import webob
from billiard.einfo import ExceptionInfo
from celery import Celery, Task, shared_task

# from typing import Union
from celery.local import Proxy
from celery.result import AsyncResult
from celery.schedules import crontab
from more import cors
from more.transaction import TransactionApp
from morepath.reify import reify
from morepath.request import Request as BaseRequest
from morepath.request import Response
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from zope.sqlalchemy import ZopeTransactionEvents
from zope.sqlalchemy import register as register_session

from . import directive, exc
from .crud.app import App as CRUDApp
from .exc import ConfigurationError
from .signal.app import SignalApp
from .sql import Base

Session = sessionmaker()
register_session(Session)


class Request(BaseRequest):
    def copy(self, *args, **kwargs):
        """
        Copy the request and environment object.

        This only does a shallow copy, except of wsgi.input
        """
        self.make_body_seekable()
        env = self.environ.copy()
        new_req = self.__class__(env, *args, **kwargs)
        new_req.copy_body()
        new_req.identity = self.identity
        return new_req


class DBSessionRequest(Request):

    _db_session: dict = {}
    _db_engines: dict = {}

    @property
    def db_session(self) -> sqlalchemy.orm.Session:
        return self.get_db_session("default")

    def get_db_engine(self, name="default"):
        # FIXME: Allow safe pooling, especially on the 
        # worker side. Currently NullPool is used
        # to force worker to clean up connections
        # upon completion of tasks
        existing = self._db_engines.get(name, None)
        if existing:
            return existing

        settings = self.app._raw_settings
        config = settings["configuration"]

        cwd = os.environ.get("MORP_WORKDIR", os.getcwd())
        os.chdir(cwd)

        key = "morpfw.storage.sqlstorage.dburi"
        if '://' in name:
            dburi = name
        else:
            if name != "default":
                key = "morpfw.storage.sqlstorage.dburi.{}".format(name)

            if not config.get(key, None):
                raise ConfigurationError("{} not found".format(key))

            dburi = config[key]
        engine = sqlalchemy.create_engine(
            dburi, poolclass=NullPool, connect_args={"options": "-c timezone=utc"}
        )

        self._db_engines[name] = engine
        return engine

    def get_db_session(self, name="default"):

        if self._db_session.get(name, None) is None:
            engine = self.get_db_engine(name)
            self._db_session[name] = Session(bind=engine)
        return self._db_session[name]


class BaseApp(CRUDApp, cors.CORSApp, SignalApp):

    request_class = Request

    @classmethod
    def all_migration_scripts(cls):
        paths = []
        for klass in cls.__mro__:
            path = getattr(klass, "migration_scripts", "migrations")
            if path:
                if not path.startswith("/"):
                    mod = sys.modules[klass.__module__]
                    filepath = getattr(mod, "__file__", None)
                    if filepath:
                        path = os.path.join(os.path.dirname(filepath), path)
                    else:
                        continue
                if os.path.exists(path):
                    if path not in paths:
                        paths.append(path)
        return paths

    def __repr__(self):
        return "<Morp Application %s:%s>" % (
            self.__class__.__module__,
            self.__class__.__name__,
        )


class App(BaseApp):
    pass


class SQLApp(TransactionApp, BaseApp):

    request_class = DBSessionRequest

    _raw_settings: dict = {}


# 	    def __init__(self, engine=None, *args, **kwargs):
# 	        super(SQLApp, self).__init__(*args, **kwargs)
# 	        self.engine = engine
# 	        self._init_engine()
#
# 	    def initdb(self, session=Session):
# 	        Base.metadata.create_all(self.engine)
#
# 	    def resetdb(self, session=Session):
# 	        Base.metadata.drop_all(self.engine)
# 	        transaction.commit()
#
