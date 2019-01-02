from .model import APIKeyCollection, APIKeyModel, APIKeySchema
from ..app import App


def get_apikey_collection(request):
    authn_provider = request.app.get_authn_provider(request)
    storage = authn_provider.get_storage(APIKeyModel, request)
    return APIKeyCollection(request, storage)


def get_apikey(request, identifier):
    collection = get_apikey_collection(request)
    return collection.get(identifier)


@App.path(model=APIKeyModel,
          path='apikey/{uuid}')
def _get_apikey(app, request, uuid):
    return get_apikey(request, uuid)


@App.path(model=APIKeyCollection,
          path='apikey')
def _get_apikey_collection(app, request):
    return get_apikey_collection(request)
