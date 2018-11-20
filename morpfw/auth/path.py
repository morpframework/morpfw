from .app import App
from .user.model import UserCollection, UserModel
from .user.path import user_collection_factory, user_factory
from .group.model import GroupModel, GroupCollection, GroupSchema
from .group.path import get_group, get_group_collection
from .apikey.model import APIKeyCollection, APIKeyModel, APIKeySchema
from .apikey.path import get_apikey, get_apikey_collection


def register_authmanager(app_class=App,
                         basepath='api/v1',
                         userpath='user', grouppath='group',
                         apikeypath='apikey'):

    @app_class.path(model=UserModel,
                    path='%s/%s/{username}' % (basepath, userpath),
                    variables=lambda obj: {
                        'username': obj.data['username']
                    })
    def _user_factory(app, request, username):
        return user_factory(request, username)

    @app_class.path(model=UserCollection,
                    path='%s/%s' % (basepath, userpath))
    def _user_collection_factory(app, request):
        return user_collection_factory(request)

    @app_class.path(model=APIKeyModel,
                    path='%s/%s/{uuid}' % (
                        basepath, apikeypath))
    def _get_apikey(app, request, uuid):
        return get_apikey(request, uuid)

    @app_class.path(model=APIKeyCollection,
                    path='%s/%s/' % (
                        basepath, apikeypath))
    def _get_apikey_collection(app, request):
        return get_apikey_collection(request)

    @app_class.path(model=GroupModel,
                    path='%s/%s/{identifier}' % (basepath, grouppath))
    def _get_group(app, request, identifier):
        return get_group(request, identifier)

    @app_class.path(model=GroupCollection,
                    path='%s/%s' % (basepath, grouppath))
    def _get_group_collection(app, request):
        return get_group_collection(request)
