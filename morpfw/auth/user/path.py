from .model import UserCollection, UserModel, UserSchema


def user_factory(request, identifier):
    collection = user_collection_factory(request)
    return collection.get(identifier)


def user_collection_factory(request):
    return UserCollection(request,
                          request.app.get_authmanager_storage(request, UserSchema))
