from .model import UserCollection, UserModel, UserSchema


def user_factory(app, request, identifier):
    collection = user_collection_factory(app, request)
    return collection.get(identifier)


def user_collection_factory(app, request):
    return UserCollection(request,
                          app.get_authmanager_storage(request, UserSchema))
