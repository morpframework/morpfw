from datetime import datetime, timedelta

import pytz


class ModelMemoizer(object):
    def __init__(self, seconds: int = None):
        self.seconds = seconds

    def __call__(self, method):
        def MemoizeWrapper(self, *args):
            klass = self.__class__
            if getattr(klass, "__memoize__", None) is None:
                klass.__memoize__ = {}
            cachemgr = klass.__memoize__
            key = hash((self.uuid, method, args))
            cache = cachemgr.get(key, None)
            if cache:
                if cache["modified"] >= self["modified"]:
                    return cache["result"]
                if timedelta:
                    if cache["modified"] >= (
                        datetime.now(tz=pytz.UTC) + timedelta(seconds=self.seconds)
                    ):
                        return cache["result"]
            result = method(self, *args)
            cachemgr[key] = {"result": result, "modified": datetime.now(tz=pytz.UTC)}
            return result

        MemoizeWrapper.__wrapped__ = method
        return MemoizeWrapper


memoize = ModelMemoizer