from .model import APIKeyCollection, APIKeyModel, APIKeySchema


def get_apikey_collection(request):
    return APIKeyCollection(request,
                            request.app.get_authmanager_storage(request, APIKeySchema))


def get_apikey(request, identifier):
    collection = get_apikey_collection(request)
    return collection.get(identifier)
