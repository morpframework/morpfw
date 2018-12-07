import re
import morepath
import dectate
from celery import Celery, Task
from celery import shared_task
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
#from typing import Union
from celery.local import Proxy
from celery.result import AsyncResult
from celery.schedules import crontab
from billiard.einfo import ExceptionInfo
from . import directive


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


class SignalApp(morepath.App):

    celery = Celery()
    _celery_subscribe = dectate.directive(directive.CelerySubscriberAction)

    @classmethod
    def async_subscribe(klass, signal: str, task_name: Optional[str] = None):
        def wrapper(wrapped):
            task = shared_task(name=task_name,  base=MorpTask)(wrapped)
            klass._celery_subscribe(signal)(task)
            return task
        return wrapper

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

    def signal(self, signal: str, **kwargs) -> Signal:
        return Signal(self, signal, **kwargs)
