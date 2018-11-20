from .model import APIKeyCollection, APIKeyModel, APIKeySchema


def apikey_collection_factory(request):
    return APIKeyCollection(request,
                            request.app.get_authmanager_storage(request, APIKeySchema))


def apikey_factory(request, identifier):
    collection = apikey_collection_factory(request)
    return collection.get(identifier)
