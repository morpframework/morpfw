from .dictprovider import DictProvider
from ..app import App
from ..storage.elasticsearchstorage import ElasticSearchStorage
from ...interfaces import ISchema


@App.dataprovider(schema=ISchema, obj=dict,
                  storage=ElasticSearchStorage)
def get_dataprovider(schema, obj, storage):
    return DictProvider(schema, obj, storage)
