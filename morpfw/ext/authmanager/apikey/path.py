from .model import APIKeyCollection, APIKeyModel, APIKeySchema


def apikey_collection_factory(app, request):
    return APIKeyCollection(request,
                            app.get_authmanager_storage(request, APIKeySchema))


def apikey_factory(app, request, identifier):
    collection = apikey_collection_factory(app, request)
    return collection.get(identifier)
