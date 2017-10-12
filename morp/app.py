import morepath
import dectate
import reg
import authmanager
from jslcrud.provider.base import Provider
from sqlalchemy.orm import sessionmaker
from more.transaction import TransactionApp
from morepath.reify import reify
from morepath.request import Request
import webob
from more import cors
from morepath.request import Response
from . import directive
from . import exc
from celery import Celery
import time
import re

Session = sessionmaker()


class Signal(object):

    def __init__(self, app, signal):
        self.app = app
        self.signal = signal

    def subscribers(self):
        self.app.config.celery_subscriber_registry.setdefault(self.signal, [])
        return self.app.config.celery_subscriber_registry[self.signal]

    def send(self, request, **kwargs):
        from .tasktracker import CeleryTaskCollection
        tasks = []
        metastore = self.app.get_celery_metastore(request)
        collection = CeleryTaskCollection(request, metastore)
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
            task = s.delay(request=req_json, **kwargs)
            meta = {
                'task': '.'.join((wrapped.__module__, wrapped.__name__)),
                'task_id': task.task_id,
                'created_ts': int(time.time() * 1000),
                'input': kwargs,
                'status': 'SUBMITTED'
            }
            collection.create(meta)
            tasks.append(task)
        return tasks


class DBSessionRequest(Request):

    @reify
    def db_session(self):
        return Session()


class BaseApp(authmanager.App, cors.CORSApp):

    celery = Celery()
    celery_task = dectate.directive(directive.CeleryTaskAction)
    celery_metastore = dectate.directive(directive.CeleryMetastoreAction)
    _celery_subscribe = dectate.directive(directive.CelerySubscriberAction)

    @reg.dispatch_method(reg.match_key('name', lambda self, name: name))
    def get_celery_task(self, name):
        raise NotImplementedError

    @classmethod
    def celery_subscribe(klass, signal):
        def wrapper(wrapped):
            task = klass.celery.task(wrapped)
            klass._celery_subscribe(signal)(task)
            return task
        return wrapper

    def celery_signal(self, signal):
        return Signal(self, signal)

    def get_celery_metastore(self, request):
        from .tasktracker import CeleryTaskSchema
        celery_settings = {
            'metastore': 'sqlstorage'
        }
        celery_config_settings = getattr(self.settings, 'celery', {})
        celery_settings.update(celery_config_settings.__dict__)
        metastore = celery_settings.get('metastore')
        metastore_options = celery_settings.get('metastore_opts', {})
        return self._get_celery_metastore(
            metastore, CeleryTaskSchema)(request, **metastore_options)

    @reg.dispatch_method(
        reg.match_key('metastore', lambda self, metastore, schema: metastore),
        reg.match_class('schema', lambda self, metastore, schema: schema))
    def _get_celery_metastore(self, metastore, schema):
        raise NotImplementedError

    def __repr__(self):
        return 'Morp Application -> %s:%s' % (self.__class__.__module__,
                                              self.__class__.__name__)


class SQLApp(TransactionApp, BaseApp):

    request_class = DBSessionRequest
