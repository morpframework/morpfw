import morepath
from .model import UserCollection, UserModel, UserSchema, CurrentUserModel
from ..app import App


def get_user(request: morepath.Request, identifier) -> UserModel:
    collection = get_user_collection(request)
    return collection.get(identifier)


def get_user_collection(request: morepath.Request) -> UserCollection:
    return UserCollection(request, storage=request.app.get_storage(UserModel, request))
