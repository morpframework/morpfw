from .jsonprovider import JsonObjectProvider
from ..app import App
from ..storage.elasticsearchstorage import ElasticSearchStorage
from ..model import Model
import jsonobject


@App.dataprovider(schema=jsonobject.JsonObject, obj=jsonobject.JsonObject,
                  storage=ElasticSearchStorage)
def get_dataprovider(schema, obj,  storage):
    return JsonObjectProvider(schema, obj, storage)
