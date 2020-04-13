import importlib
import json
import os
import re
import threading
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from uuid import uuid4

import dectate
import morepath
import transaction
from billiard.einfo import ExceptionInfo
from celery import Celery, Task, shared_task
from celery.contrib import rdb

# from typing import Union
from celery.local import Proxy
from celery.result import AsyncResult
from celery.schedules import crontab

from . import directive
from . import signal as event_signal

ALLOWED_ENVIRONMENT_KEYS = [
    "USER",
    "SCRIPT_NAME",
    "PATH_INFO",
    "QUERY_STRING",
    "SERVER_NAME",
    "SERVER_PORT",
    "REMOTE_HOST",
    "HTTP_HOST",
    "SERVER_PROTOCOL",
    "wsgi.url_scheme",
]


class MorpTask(Task):
    abstract = True

    def after_return(
        self,
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
        for k, v in request.environ.items():
            if k in ALLOWED_ENVIRONMENT_KEYS:
                envs[k] = v

        req_json = {
            "headers": dict(request.headers),
            "environ": envs,
            # "text": request.text,
        }

        subs = self.subscribers()
        for s in subs:
            task = s.apply_async(
                kwargs=dict(request=req_json, **kwargs), **self.signal_opts
            )
            task.__signal__ = self.signal
            task.__params__ = kwargs
            self.app.dispatcher(event_signal.TASK_SUBMITTED).dispatch(request, task)
            tasks.append(task)
        return tasks


def periodic_transaction_handler(name, func):
    def transaction_wrapper(task):
        task.request.__job_name__ = name
        settings = json.loads(os.environ["MORP_SETTINGS"])
        mod, clsname = settings["application"]["class"].split(":")
        app_class = getattr(importlib.import_module(mod), clsname)
        app_class.commit()
        app = app_class()
        server_url = settings.get("server", {}).get("server_url", "http://localhost")
        parsed = urlparse(server_url)
        environ = {
            "PATH_INFO": "/",
            "wsgi.url_scheme": parsed.scheme,
            "SERVER_PROTOCOL": "HTTP/1.1",
            "HTTP_HOST": parsed.netloc,
        }
        req = app.request_class(app=app, environ=environ)
        transaction.begin()

        req.app.dispatcher(event_signal.SCHEDULEDTASK_STARTING).dispatch(
            req, task.request
        )
        savepoint = transaction.savepoint()
        failed = False
        try:
            res = func(req)
            req.app.dispatcher(event_signal.SCHEDULEDTASK_COMPLETED).dispatch(
                req, task.request
            )
        except Exception:
            savepoint.rollback()
            failed = True
            raise
        finally:
            if failed:
                req.app.dispatcher(event_signal.SCHEDULEDTASK_FAILED).dispatch(
                    req, task.request
                )
            req.app.dispatcher(event_signal.SCHEDULEDTASK_FINALIZED).dispatch(
                req, task.request
            )
            transaction.commit()

        return res

    return transaction_wrapper


def transaction_handler(func):
    def transaction_wrapper(task, request, **kwargs):
        settings = json.loads(os.environ["MORP_SETTINGS"])
        mod, clsname = settings["application"]["class"].split(":")
        app_class = getattr(importlib.import_module(mod), clsname)
        app = app_class()
        req = app.request_class(app=app, **request)
        transaction.begin()
        req.app.dispatcher(event_signal.TASK_STARTING).dispatch(req, task.request)
        savepoint = transaction.savepoint()
        failed = False
        try:
            res = func(req, **kwargs)
            req.app.dispatcher(event_signal.TASK_COMPLETED).dispatch(req, task.request)
        except Exception:
            savepoint.rollback()
            failed = True
            raise
        finally:
            if failed:
                req.app.dispatcher(event_signal.TASK_FAILED).dispatch(req, task.request)
            req.app.dispatcher(event_signal.TASK_FINALIZED).dispatch(req, task.request)
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
                name = ".".join([wrapped.__module__, wrapped.__name__])
            else:
                name = task_name
            func = transaction_handler(wrapped)
            task = shared_task(name=name, base=MorpTask, bind=True)(func)
            klass._celery_subscribe(signal)(task)
            return task

        return wrapper

    @classmethod
    def cron(
        klass,
        name: str,
        minute: str = "*",
        hour: str = "*",
        day_of_week: str = "*",
        day_of_month: str = "*",
        month_of_year: str = "*",
    ):
        def wrapper(wrapped):
            func = periodic_transaction_handler(name, wrapped)
            task_name = ".".join([wrapped.__module__, wrapped.__name__])
            task = shared_task(name=task_name, base=MorpTask, bind=True)(func)
            klass.celery.conf.beat_schedule[name] = {
                "task": task_name,
                "schedule": crontab(
                    minute=minute,
                    hour=hour,
                    day_of_week=day_of_week,
                    day_of_month=day_of_month,
                    month_of_year=month_of_year,
                ),
            }
            return task

        return wrapper

    @classmethod
    def periodic(klass, name: str, seconds: int = 1):
        def wrapper(wrapped):
            func = periodic_transaction_handler(name, wrapped)
            task_name = ".".join([wrapped.__module__, wrapped.__name__])
            task = shared_task(name=task_name, base=MorpTask, bind=True)(func)
            klass.celery.conf.beat_schedule[name] = {
                "task": task_name,
                "schedule": seconds,
            }
            return task

        return wrapper
