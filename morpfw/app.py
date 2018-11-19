import morepath
import dectate
import reg
from . import authmanager
from .crud.provider.base import Provider
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool, QueuePool
from more.transaction import TransactionApp
from morepath.reify import reify
from morepath.request import Request
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
from .ext.authmanager.user.model import UserCollection, UserSchema
from .ext.authmanager.group.model import GroupCollection, GroupSchema
from .ext.authmanager.exc import UserExistsError
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


Session = sessionmaker(extension=ZopeTransactionExtension())


class MorpTask(Task):
    abstract = True

    def after_return(self,
                     status: str,
                     retval: Any,
                     task_id: str,
                     args: List,
                     kwargs: Dict,
                     einfo: Optional[ExceptionInfo],
                     ):
        pass


class Signal(object):

    def __init__(self, app: morepath.App, signal: str, **kwargs):
        self.app = app
        self.signal = signal
        self.signal_opts = kwargs

    def subscribers(self) -> List[Proxy]:
        self.app.config.celery_subscriber_registry.setdefault(self.signal, [])
        return self.app.config.celery_subscriber_registry[self.signal]

    def send(self, request: morepath.Request, **kwargs) -> List[AsyncResult]:
        tasks = []
        envs = {}
        allcaps = re.compile(r'^[A-Z_]+$')
        for k, v in request.environ.items():
            if allcaps.match(k):
                envs[k] = v
            elif k in ['wsgi.url_scheme']:
                envs[k] = v

        req_json = {
            'headers': dict(request.headers),
            'environ': envs,
            'text': request.text,
        }

        subs = self.subscribers()
        for s in subs:
            wrapped = s.__wrapped__
            task = s.apply_async(kwargs=dict(request=req_json, **kwargs),
                                 **self.signal_opts)
            tasks.append(task)
        return tasks


class DBSessionRequest(Request):

    _db_session = None

    @property
    def db_session(self) -> sqlalchemy.orm.Session:
        if self._db_session is None:
            self._db_session = Session()
        return self._db_session


class BaseApp(authmanager.App, cors.CORSApp):

    celery = Celery()
    _celery_subscribe = dectate.directive(directive.CelerySubscriberAction)
    _raw_settings: dict = {}

    @reg.dispatch_method(reg.match_key('name', lambda self, name: name))
    def get_celery_task(self, name):
        raise NotImplementedError

    @classmethod
    def celery_subscribe(klass, signal, task_name: Optional[str] = None):
        warnings.warn(
            "celery_subscibe is deprecated, use async_subscribe",
            DeprecationWarning)
        return klass.async_subscribe(signal, task_name)

    @classmethod
    def async_subscribe(klass, signal: str, task_name: Optional[str] = None):
        def wrapper(wrapped):
            task = shared_task(name=task_name,  base=MorpTask)(wrapped)
            klass._celery_subscribe(signal)(task)
            return task
        return wrapper

    @classmethod
    def celery_cron(klass, name, minute='*', hour='*', day_of_week='*',
                    day_of_month='*', month_of_year='*'):
        warnings.warn("celery_cron is deprecated, use cron",
                      DeprecationWarning)
        return klass.cron(name, minute, hour, day_of_week,
                          day_of_month, month_of_year)

    @classmethod
    def cron(klass, name: str, minute: str = '*', hour: str = '*', day_of_week: str = '*',
             day_of_month: str = '*', month_of_year: str = '*'):
        def wrapper(wrapped):
            task = shared_task()(wrapped)
            klass.celery.conf.beat_schedule[name] = {
                'task': '.'.join([wrapped.__module__, wrapped.__name__]),
                'schedule': crontab(minute=minute, hour=hour,
                                    day_of_week=day_of_week,
                                    day_of_month=day_of_month,
                                    month_of_year=month_of_year)
            }
            return task
        return wrapper

    def celery_signal(self, signal, **kwargs):
        warnings.warn("celery_signal is deprecated, use signal",
                      DeprecationWarning)
        return self.signal(signal, **kwargs)

    def signal(self, signal: str, **kwargs) -> Signal:
        return Signal(self, signal, **kwargs)

    def __repr__(self):
        return 'Morp Application -> %s:%s' % (self.__class__.__module__,
                                              self.__class__.__name__)


def create_admin(app: morepath.App, username: str, password: str, email: str, session=Session):
    request = app.request_class(
        app=app, environ={'PATH_INFO': '/'})

    transaction.manager.begin()
    context = UserCollection(
        request, app.get_authmanager_storage(request, UserSchema))
    userobj = context.create({'username': username,
                              'password': password,
                              'email': email,
                              'state': 'active'})
    gstorage = app.get_authmanager_storage(
        request, GroupSchema)
    group = gstorage.get('__default__')
    group.add_members([username])
    group.grant_member_role(username, 'administrator')
    transaction.manager.commit()
    return userobj


class SQLApp(TransactionApp, BaseApp):

    request_class = DBSessionRequest

    _engine = None

    def __init__(self, *args, **kwargs):
        super(SQLApp, self).__init__(*args, **kwargs)
        self._init_engine()

    def _init_engine(self, session=Session) -> Engine:

        settings = self._raw_settings

        if self._engine is not None:
            return self._engine

        register_session(session)

        # initialize SQLAlchemy
        if 'sqlalchemy' not in settings:
            raise ConfigurationError('SQLAlchemy settings not found')
        if 'sqlalchemy' in settings:
            cwd = os.environ.get('MORP_WORKDIR', os.getcwd())
            os.chdir(cwd)
            dburi = settings['sqlalchemy']['dburi'] % {'here': cwd}
            engine = sqlalchemy.create_engine(dburi, poolclass=NullPool)
            session.configure(bind=engine)

        self._engine = engine
        return engine

    def initdb(self, session=Session):
        Base.metadata.create_all(self._engine)
