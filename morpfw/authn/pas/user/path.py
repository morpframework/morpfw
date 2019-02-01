import morepath
from .model import UserCollection, UserModel, UserSchema, CurrentUserModel
from ..app import App


def get_user(request: morepath.Request, identifier) -> UserModel:
    collection = get_user_collection(request)
    return collection.get(identifier)


def get_user_collection(request: morepath.Request) -> UserCollection:
    authprovider = request.app.get_authn_provider(request)
    return UserCollection(request, storage=authprovider.get_storage(UserModel, request))


@App.path(model=UserModel,
          path='user/{username}',
          variables=lambda obj: {
              'username': obj.data['username']
          })
def _get_user(app, request, username):
    return get_user(request, username)


@App.path(model=UserCollection,
          path='user')
def _get_user_collection(app, request):
    return get_user_collection(request)


@App.path(model=CurrentUserModel, path='self')
def _get_current_user(app, request):
    userid = request.identity.userid
    if not userid:
        return None
    col = get_user_collection(request)
    user = col.get_by_userid(userid)
    if not user:
        return None
    return CurrentUserModel(request, user.storage, user.data.data)
