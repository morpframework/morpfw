from .model import APIKeyCollection, APIKeyModel
from .schema import APIKeySchema
from .path import get_apikey, get_apikey_collection
from ..app import App


@App.typeinfo(name='morpfw.pas.apikey', schema=APIKeySchema)
def get_typeinfo(request):
    return {
        'title': 'API Key',
        'description': 'API Key type',
        'schema': APIKeySchema,
        'collection': APIKeyCollection,
        'collection_factory': get_apikey_collection,
        'model': APIKeyModel,
        'model_factory': get_apikey,
        'internal': True,
    }
