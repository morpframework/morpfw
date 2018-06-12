from .dictprovider import DictProvider
from ..app import App
from ..storage.elasticsearchstorage import ElasticSearchStorage
import jsl


@App.jslcrud_dataprovider(schema=jsl.Document, obj=dict,
                          storage=ElasticSearchStorage)
def get_dataprovider(schema, obj, storage):
    return DictProvider(schema, obj, storage)
