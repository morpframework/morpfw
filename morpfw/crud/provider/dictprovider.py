from ..app import App
from .base import Provider
from ..types import datestr
from ..storage.memorystorage import MemoryStorage
from dateutil.parser import parse as parse_date
import datetime
import jsonobject

_MARKER: list = []


class DictProvider(Provider):

    def __init__(self, schema, data, storage):
        self.schema = schema
        self.data = data
        self.storage = storage
        self.changed = False

    def __getitem__(self, key):
        if isinstance(self.schema.properties()[key], jsonobject.DateTimeProperty):
            data = self.data[key]
            if isinstance(data, str):
                return parse_date(data)
            return data
        if key not in self.data.keys():
            default = self.schema.properties()[key].default
            return default()
        return self.data[key]

    def __setitem__(self, key, value):
        if isinstance(self.schema.properties()[key], jsonobject.DateTimeProperty):
            if value and not isinstance(value, datetime.datetime):
                value = parse_date(value)
        self.data[key] = value
        self.changed = True

    def __delitem__(self, key):
        del self.data[key]
        self.changed = True

    def setdefault(self, key, value):
        r = self.data.setdefault(key, value)
        self.changed = True
        return r

    def get(self, key, default=_MARKER):
        if default is _MARKER:
            return self.data.get(key)
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.changed = True

    def items(self):
        return self.data.items()

    def keys(self):
        return self.data.keys()

    def as_dict(self):
        result = {}
        for k, v in obj.data.items():
            result[k] = v
        return result

    def as_json(self):
        result = {}
        for k, v in self.data.items():
            if isinstance(v, datetime.datetime):
                result[k] = datestr(v.isoformat())
            else:
                result[k] = v
        return result


@App.dataprovider(schema=jsonobject.JsonObject, obj=dict, storage=MemoryStorage)
def get_dataprovider(schema, obj, storage):
    return DictProvider(schema, obj, storage)


@App.jsonprovider(obj=DictProvider)
def get_jsonprovider(obj):
    return obj.as_json()
