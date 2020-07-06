from datetime import datetime

import colander
from inverter.common import dataclass_get_type

from ...interfaces import IDataProvider, ISchema
from ..app import App
from ..storage.elasticsearchstorage import ElasticSearchStorage
from .dictprovider import DictProvider


@App.dataprovider(schema=ISchema, obj=dict, storage=ElasticSearchStorage)
def get_dataprovider(schema, obj, storage):
    return ElasticSearchProvider(schema, obj, storage)


_MARKER = object()


def _deserialize(schema, key, value):
    res = schema[key].deserialize(value)
    if res in [colander.drop, colander.null]:
        return None
    return res


class ElasticSearchProvider(DictProvider):
    pass
