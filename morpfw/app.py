import morepath
import dectate
import reg
from . import authmanager
from .jslcrud.provider.base import Provider
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
from .authmanager.model.user import UserCollection, UserSchema
from .authmanager.model.group import GroupCollection, GroupSchema
from .authmanager.exc import UserExistsError
import transaction
import os
from zope.sqlalchemy import register as register_session
import transaction
from zope.sqlalchemy import ZopeTransactionExtension
from .exc import ConfigurationError
import warnings


Session = sessionmaker(extension=ZopeTransactionExtension())


class SqlAlchemyTask(Task):
    abstract = True

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        pass


class Signal(object):

    def __init__(self, app, signal, **kwargs):
        self.app = app
        self.signal = signal
        self.signal_opts = kwargs

    def subscribers(self):
        self.app.config.celery_subscriber_registry.setdefault(self.signal, [])
        return self.app.config.celery_subscriber_registry[self.signal]

    def send(self, request, **kwargs):
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
    def db_session(self):
        if self._db_session is None:
            self._db_session = Session()
        return self._db_session


class BaseApp(authmanager.App, cors.CORSApp):

    celery = Celery()
    _celery_subscribe = dectate.directive(directive.CelerySubscriberAction)
    _raw_settings = {}

    @reg.dispatch_method(reg.match_key('name', lambda self, name: name))
    def get_celery_task(self, name):
        raise NotImplementedError

    @classmethod
    def celery_subscribe(klass, signal, task_name=None):
        warnings.warn(
            "celery_subscibe is deprecated, use async_subscribe",
            DeprecationWarning)
        return klass.async_subscribe(signal, task_name)

    @classmethod
    def async_subscribe(klass, signal, task_name=None):
        def wrapper(wrapped):
            task = shared_task(name=task_name,  base=SqlAlchemyTask)(wrapped)
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
    def cron(klass, name, minute='*', hour='*', day_of_week='*',
             day_of_month='*', month_of_year='*'):
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

    def signal(self, signal, **kwargs):
        return Signal(self, signal, **kwargs)

    def __repr__(self):
        return 'Morp Application -> %s:%s' % (self.__class__.__module__,
                                              self.__class__.__name__)


def create_admin(app, username, password, session=Session):
    request = app.request_class(
        app=app, environ={'PATH_INFO': '/'})

    transaction.manager.begin()
    context = UserCollection(
        request, app.get_authmanager_storage(request, UserSchema))
    userobj = context.create({'username': username,
                              'password': password,
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

    def _init_engine(self, session=Session):

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
