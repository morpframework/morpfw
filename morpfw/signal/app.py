import re
import morepath
import dectate
import json
import os
from urllib.parse import urlparse
from celery import Celery, Task
from celery import shared_task
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
# from typing import Union
from celery.local import Proxy
from celery.result import AsyncResult
from celery.schedules import crontab
from billiard.einfo import ExceptionInfo
import transaction
from . import directive
from uuid import uuid4


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


class AsyncDispatcher(object):

    def __init__(self, app: morepath.App, signal: str, **kwargs):
        self.app = app
        self.signal = signal
        self.signal_opts = kwargs

    def subscribers(self) -> List[Proxy]:
        self.app.config.celery_subscriber_registry.setdefault(self.signal, [])
        return self.app.config.celery_subscriber_registry[self.signal]

    def dispatch(self, request: morepath.Request, **kwargs) -> List[AsyncResult]:
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
            task = s.apply_async(kwargs=dict(request=req_json, **kwargs),
                                 **self.signal_opts)
            tasks.append(task)
        return tasks


def periodic_transaction_handler(app_class, func):
    def transaction_wrapper():
        settings = json.loads(os.environ['MORP_SETTINGS'])
        app_class._raw_settings = settings
        app = app_class()
        server_url = settings.get('server', {}).get(
            'server_url', 'http://localhost')
        parsed = urlparse(server_url)
        environ = {
            'PATH_INFO': '/',
            'wsgi.url_scheme': parsed.scheme,
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'HTTP_HOST': parsed.netloc,
        }
        req = app.request_class(app=app, environ=environ)
        transaction.begin()
        savepoint = transaction.savepoint()
        try:
            res = func(req)
        except:
            savepoint.rollback()
            raise
        finally:
            transaction.commit()

        return res
    return transaction_wrapper


def transaction_handler(app_class, func):
    def transaction_wrapper(request, obj):
        settings = json.loads(os.environ['MORP_SETTINGS'])
        app_class._raw_settings = settings
        app = app_class()
        req = app.request_class(app=app, **request)
        transaction.begin()
        savepoint = transaction.savepoint()
        try:
            res = func(req, obj)
        except:
            savepoint.rollback()
            raise
        finally:
            transaction.commit()

        return res
    return transaction_wrapper


class SignalApp(morepath.App):

    celery = Celery()
    _celery_subscribe = dectate.directive(directive.CelerySubscriberAction)

    def async_dispatcher(self, signal: str, **kwargs) -> AsyncDispatcher:
        return AsyncDispatcher(self, signal, **kwargs)

    @classmethod
    def async_subscribe(klass, signal: str, task_name: Optional[str] = None):
        def wrapper(wrapped):
            if task_name is None:
                name = '.'.join([wrapped.__module__, wrapped.__name__])
            else:
                name = task_name
            func = transaction_handler(klass, wrapped)
            task = shared_task(name=name,  base=MorpTask)(func)
            klass._celery_subscribe(signal)(task)
            return task
        return wrapper

    @classmethod
    def cron(klass, name: str, minute: str = '*', hour: str = '*', day_of_week: str = '*',
             day_of_month: str = '*', month_of_year: str = '*'):
        def wrapper(wrapped):
            func = periodic_transaction_handler(klass, wrapped)
            task_name = '.'.join([wrapped.__module__, wrapped.__name__])
            task = shared_task(name=task_name, base=MorpTask)(func)
            klass.celery.conf.beat_schedule[name] = {
                'task': task_name,
                'schedule': crontab(minute=minute, hour=hour,
                                    day_of_week=day_of_week,
                                    day_of_month=day_of_month,
                                    month_of_year=month_of_year)
            }
            return task
        return wrapper

    @classmethod
    def periodic(klass, name: str, seconds: int = 1):
        def wrapper(wrapped):
            func = periodic_transaction_handler(klass, wrapped)
            task_name = '.'.join([wrapped.__module__, wrapped.__name__])
            task = shared_task(name=task_name, base=MorpTask)(func)
            klass.celery.conf.beat_schedule[name] = {
                'task': task_name,
                'schedule': seconds
            }
            return task
        return wrapper
