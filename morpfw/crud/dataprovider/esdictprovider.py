from ...interfaces import IDataProvider, ISchema
from ..app import App
from ..schemaconverter.common import dataclass_get_type
from ..schemaconverter.dataclass2colanderjson import dataclass_to_colanderjson
from ..storage.elasticsearchstorage import ElasticSearchStorage
from .dictprovider import DictProvider


@App.dataprovider(schema=ISchema, obj=dict, storage=ElasticSearchStorage)
def get_dataprovider(schema, obj, storage):
    return ElasticSearchProvider(schema, obj, storage)


_MARKER = object()


class ElasticSearchProvider(DictProvider):
    def __init__(self, schema, data, storage):
        super().__init__(schema, data, storage)

    def __getitem__(self, key):
        cschema = dataclass_to_colanderjson(self.schema, include_fields=[key],
                request=self.storage.request)
        return cschema().deserialize(self.data)[key]

    def __setitem__(self, key, value):
        cschema = dataclass_to_colanderjson(self.schema, include_fields=[key],
                request=self.storage.request)
        value = cschema().serialize({key: value})[key]
        self.data[key] = value
        self.changed = True

    def setdefault(self, key, value):
        cschema = dataclass_to_colanderjson(self.schema, include_fields=[key],
                request=self.storage.request)
        value = cschema().serialize({key: value})[key]
        self.changed = True
        return r

    def get(self, key, default=_MARKER):
        if key == "id":
            return self.data.get(key)

        cschema = dataclass_to_colanderjson(self.schema, include_fields=[key],
                request=self.storage.request)

        if default is _MARKER:
            result = self.data.get(key)
        else:
            result = self.data.get(key, default)

        return cschema().deserialize({key: result})[key]

    def set(self, key, value):
        cschema = dataclass_to_colanderjson(self.schema, include_fields=[key],
                request=self.storage.request)
        value = cschema().serialize({key: value})[key]
        self.data[key] = value
        self.changed = True

    def items(self):
        cschema = dataclass_to_colanderjson(self.schema,
                request=self.storage.request)
        return cschema().deserialize(self.data).items()

    def as_dict(self):
        cschema = dataclass_to_colanderjson(self.schema,
                request=self.storage.request)
        return cschema().deserialize(self.data)

    def as_json(self):
        return self.data
