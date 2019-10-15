from .model import APIKeyCollection, APIKeyModel, APIKeySchema
from ..app import App


def get_apikey_collection(request):
    storage = request.app.get_storage(APIKeyModel, request)
    return APIKeyCollection(request, storage)


def get_apikey(request, identifier):
    collection = get_apikey_collection(request)
    return collection.get(identifier)
