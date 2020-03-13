import inspect
from datetime import datetime, timedelta

import pytz


class ModelMemoizer(object):
    def __init__(self, seconds: int = None):
        self.seconds = seconds

    def __call__(self, method):
        seconds = self.seconds

        def MemoizeWrapper(self, *args):
            klass = self.__class__
            if getattr(klass, "__memoize__", None) is None:
                klass.__memoize__ = {}
            cachemgr = klass.__memoize__
            key = hash((self.__class__, method, self.uuid, args))
            cache = cachemgr.get(key, None)
            if cache:
                if cache["modified"] >= self["modified"]:
                    return cache["result"]
                if timedelta:
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
    def __init__(self, seconds: int = None, environ_key="morpfw.memoize"):
        self.seconds = seconds
        self.environ_key = environ_key

    def __call__(self, method):
        environ_key = self.environ_key
        seconds = self.seconds

        def RequestMemoizeWrapper(self, *args):
            nomemoize = self.request.environ.get("morpfw.nomemoize", False)
            if nomemoize is not None:
                return method(*args)
            nomemoize = self.request.headers.get("X-MORP-NOMEMOIZE", None)
            if nomemoize is not None:
                return method(*args)
            self.request.environ.setdefault(environ_key, {})
            cachemgr = self.request.environ[environ_key]
            key = hash((self.__class__, method, self.uuid, args))
            cache = cachemgr.get(key, None)
            if cache:
                if cache["modified"] >= self["modified"]:
                    return cache["result"]
                if timedelta:
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
