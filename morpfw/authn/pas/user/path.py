import morepath
from .model import UserCollection, UserModel, UserSchema, CurrentUserModel
from ..app import App


def get_user(request: morepath.Request, identifier) -> UserModel:
    collection = get_user_collection(request)
    return collection.get(identifier)


def get_user_collection(request: morepath.Request) -> UserCollection:
    return UserCollection(request, storage=request.app.get_storage(UserModel, request))


def get_current_user(request: morepath.Request) -> UserModel:
    userid = request.identity.userid
    collection = get_user_collection(request)
    return collection.get_by_userid(userid)


def refresh_nonce_handler(request, userid):
    collection = get_user_collection(request)
    return collection.get_by_userid(userid)['nonce']
