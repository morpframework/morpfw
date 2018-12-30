import morepath
import dectate
import reg
from . import auth as authmanager
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
from .auth.user.model import UserCollection, UserSchema
from .auth.group.model import GroupCollection, GroupSchema
from .auth.exc import UserExistsError
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


class DBSessionRequest(Request):

    _db_session = None

    @property
    def db_session(self) -> sqlalchemy.orm.Session:
        if self._db_session is None:
            self._db_session = Session()
        return self._db_session


class BaseApp(CRUDApp, cors.CORSApp, SignalApp):

    authnz_provider = dectate.directive(directive.AuthnzProviderAction)
    request_class = Request

    @reg.dispatch_method()
    def get_authnz_provider(self):
        raise NotImplementedError

    def __repr__(self):
        return 'Morp Application -> %s:%s' % (self.__class__.__module__,
                                              self.__class__.__name__)


def create_admin(app: morepath.App, username: str, password: str, email: str, session=Session):
    authapp = app.get_authnz_provider()
    authapp.root = app
    request = authapp.request_class(app=authapp, environ={'PATH_INFO': '/'})

    transaction.manager.begin()
    get_authn_storage = authapp.get_authn_storage
    usercol = UserCollection(request, get_authn_storage(request, UserSchema))
    userobj = usercol.create({'username': username,
                              'password': password,
                              'email': email,
                              'state': 'active'})
    gstorage = get_authn_storage(request, GroupSchema)
    group = gstorage.get('__default__')
    group.add_members([userobj.userid])
    group.grant_member_role(userobj.userid, 'administrator')
    transaction.manager.commit()
    return userobj


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
