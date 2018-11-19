from .dictprovider import DictProvider
from ..app import App
from ..storage.elasticsearchstorage import ElasticSearchStorage
import jsonobject


@App.dataprovider(schema=jsonobject.JsonObject, obj=dict,
                  storage=ElasticSearchStorage)
def get_dataprovider(schema, obj, storage):
    return DictProvider(schema, obj, storage)
