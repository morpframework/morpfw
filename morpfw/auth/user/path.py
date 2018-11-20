from .model import UserCollection, UserModel, UserSchema


def get_user(request, identifier):
    collection = get_user_collection(request)
    return collection.get(identifier)


def get_user_collection(request):
    return UserCollection(request,
                          request.app.get_authmanager_storage(request, UserSchema))
