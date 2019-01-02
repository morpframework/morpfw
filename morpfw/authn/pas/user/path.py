from .model import UserCollection, UserModel, UserSchema
from ..app import App


def get_user(request, identifier):
    collection = get_user_collection(request)
    return collection.get(identifier)


def get_user_collection(request):
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
