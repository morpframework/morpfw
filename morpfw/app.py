import morepath
import dectate
import reg
from .crud.provider.base import Provider
from .crud.app import App as CRUDApp
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool, QueuePool
from more.transaction import TransactionApp
from morepath.reify import reify
from morepath.request import Request as BaseRequest
import webob
from more import cors
from morepath.request import Response
from . import directive
from . import exc
from celery import Celery, Task
from celery import shared_task
from celery.schedules import crontab
import time
import re
import sqlalchemy
from .sql import Base
import transaction
import os
from zope.sqlalchemy import register as register_session
import transaction
from zope.sqlalchemy import ZopeTransactionExtension
from .exc import ConfigurationError
import warnings
import sqlalchemy.orm
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
#from typing import Union
from celery.local import Proxy
from celery.result import AsyncResult
from sqlalchemy.engine.base import Engine
from billiard.einfo import ExceptionInfo
from .signal.app import SignalApp
import reg

Session = sessionmaker(extension=ZopeTransactionExtension())


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

    def get_authn_request(self):
        app = self.app.get_authn_provider(self)
        return self.copy(app=app)


class DBSessionRequest(Request):

    _db_session = None

    @property
    def db_session(self) -> sqlalchemy.orm.Session:
        if self._db_session is None:
            self._db_session = Session()
        return self._db_session


class BaseApp(CRUDApp, cors.CORSApp, SignalApp):

    authn_provider = dectate.directive(directive.AuthnProviderAction)
    request_class = Request

    def get_authn_provider(self, request):
        authn_app = self._get_authn_provider()
        authn_app.root = request.app.root
        authn_app.parent = request.app
        return authn_app

    @reg.dispatch_method()
    def _get_authn_provider(self):
        raise NotImplementedError

    def __repr__(self):
        return 'Morp Application -> %s:%s' % (self.__class__.__module__,
                                              self.__class__.__name__)


class SQLApp(TransactionApp, BaseApp):

    request_class = DBSessionRequest

    engine = None
    _raw_settings: dict = {}

    def __init__(self, engine=None, *args, **kwargs):
        super(SQLApp, self).__init__(*args, **kwargs)
        self.engine = engine
        self._init_engine()

    def _init_engine(self, session=Session) -> Engine:

        settings = self._raw_settings

        if self.engine is not None:
            return self.engine

        register_session(session)
        # initialize SQLAlchemy
        if not settings['application']['dburi']:
            raise ConfigurationError('SQLAlchemy settings not found')

        cwd = os.environ.get('MORP_WORKDIR', os.getcwd())
        os.chdir(cwd)
        dburi = settings['application']['dburi'] % {'here': cwd}
        engine = sqlalchemy.create_engine(dburi, poolclass=NullPool)
        session.configure(bind=engine)

        self.engine = engine
        return engine

    def initdb(self, session=Session):
        Base.metadata.create_all(self.engine)
