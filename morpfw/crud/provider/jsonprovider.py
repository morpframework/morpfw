from ..app import App
from .base import Provider
from ..types import datestr
from ..storage.memorystorage import MemoryStorage
from ..model import Model
import jsonobject
import datetime

_MARKER = []


class JsonObjectProvider(Provider):

    def __init__(self, schema, data, storage):
        self.schema = schema
        self.data = data
        self.storage = storage
        self.changed = False

    def __getitem__(self, key):
        if isinstance(self.schema.properties()[key], jsonobject.DateTimeProperty):
            value = self.data[key]
            assert isinstance(value, datetime.datetime) or value is None
            return value
        return self.data[key]

    def __setitem__(self, key, value):
        if isinstance(self.schema.properties()[key], jsonobject.DateTimeProperty):
            assert isinstance(value, datetime.datetime) or value is None

        self.data[key] = value
        self.changed = True

    def __delitem__(self, key):
        del self.data[key]
        self.changed = True

    def get(self, key, default=_MARKER):
        if default is _MARKER:
            return self.data[key]
        return self.data[key]

    def set(self, key, value):
        self.data[key] = value
        self.changed = True

    def items(self):
        return self.data.items()

    def keys(self):
        return self.data.keys()

    def to_json(self):
        return self.data.to_json()


@App.dataprovider(schema=jsonobject.JsonObject,
                  obj=jsonobject.JsonObject,
                  storage=MemoryStorage)
def get_dataprovider(model, obj, storage):
    return JsonObjectProvider(model, obj, storage)


@App.jsonprovider(obj=JsonObjectProvider)
def get_jsonprovider(obj):
    return obj.data.to_json()
