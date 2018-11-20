from .model import APIKeyCollection, APIKeyModel, APIKeySchema
from ..app import App


def get_apikey_collection(request):
    return APIKeyCollection(request,
                            request.app.get_authmanager_storage(request, APIKeySchema))


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
