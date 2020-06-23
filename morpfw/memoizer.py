import inspect
import threading
from datetime import datetime, timedelta

import pytz

from .interfaces import ICollection, IModel

threadlocal = threading.local()


class ModelMemoizer(object):
    def __init__(self, seconds: int = None):
        self.seconds = seconds

    def __call__(self, method):
        seconds = self.seconds

        def MemoizeWrapper(self, *args):
            klass = self.__class__
            nomemoize = self.request.environ.get("morpfw.nomemoize", False)
            if nomemoize:
                return method(self, *args)
            nomemoize = self.request.headers.get("X-MORP-NOMEMOIZE", None)
            if nomemoize is not None:
                return method(self, *args)
            if getattr(klass, "__memoize__", None) is None:

                memoizer = getattr(threadlocal, "mfw_classmemoize", None)
                if memoizer is None:
                    memoizer = {}
                    threadlocal.mfw_classmemoize = memoizer
                klass.__memoize__ = memoizer
            cachemgr = klass.__memoize__
            if isinstance(self, IModel):
                key = hash((self.__class__, method, self.uuid, args))
            elif isinstance(self, ICollection):
                key = hash((self.__class__, method, args))
            else:
                raise AssertionError(
                    "Memoization is only supported on IModel and ICollection instances"
                )
            cache = cachemgr.get(key, None)
            if cache:
                if isinstance(self, IModel) and cache["modified"] >= self["modified"]:
                    return cache["result"]

                if seconds:
                    if cache["modified"] >= (
                        datetime.now(tz=pytz.UTC) + timedelta(seconds=seconds)
                    ):
                        return cache["result"]

            result = method(self, *args)
            cachemgr[key] = {"result": result, "modified": datetime.now(tz=pytz.UTC)}
            return result

        MemoizeWrapper.__wrapped__ = method
        return MemoizeWrapper


class ModelRequestMemoizer(object):

    environ_key = "morpfw.memoize"

    def __init__(self, seconds: int = None):
        self.seconds = seconds

    def __call__(self, method):
        environ_key = self.environ_key
        seconds = self.seconds

        def RequestMemoizeWrapper(self, *args):
            nomemoize = self.request.environ.get("morpfw.nomemoize", False)
            if nomemoize:
                return method(self, *args)
            nomemoize = self.request.headers.get("X-MORP-NOMEMOIZE", None)
            if nomemoize is not None:
                return method(self, *args)
            self.request.environ.setdefault(environ_key, {})
            cachemgr = self.request.environ[environ_key]
            if isinstance(self, IModel):
                key = hash((self.__class__, method, self.uuid, args))
            elif isinstance(self, ICollection):
                key = hash((self.__class__, method, args))
            else:
                raise AssertionError(
                    "Memoization is only supported on IModel and ICollection instances"
                )
            cache = cachemgr.get(key, None)
            if cache:
                if isinstance(self, IModel) and cache["modified"] >= self["modified"]:
                    return cache["result"]

                if seconds:
                    if cache["modified"] >= (
                        datetime.now(tz=pytz.UTC) + timedelta(seconds=seconds)
                    ):
                        return cache["result"]

            result = method(self, *args)
            cachemgr[key] = {"result": result, "modified": datetime.now(tz=pytz.UTC)}
            return result

        RequestMemoizeWrapper.__wrapped__ = method
        return RequestMemoizeWrapper


memoize = ModelMemoizer
requestmemoize = ModelRequestMemoizer
