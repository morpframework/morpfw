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

from . import directive, exc
from .crud.app import App as CRUDApp
from .exc import ConfigurationError
from .request import DBSessionRequest, Request
from .signal.app import SignalApp


class BaseApp(CRUDApp, cors.CORSApp, SignalApp):

    home_env = 'MFW_HOME'
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
