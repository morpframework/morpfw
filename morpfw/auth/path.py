from .app import App
from .user.model import UserCollection, UserModel
from .user.path import user_collection_factory, user_factory
from .group.model import GroupModel, GroupCollection, GroupSchema
from .group.path import group_model_factory, group_collection_factory
from .apikey.model import APIKeyCollection, APIKeyModel, APIKeySchema
from .apikey.path import apikey_factory, apikey_collection_factory


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
    def _apikey_factory(app, request, uuid):
        return apikey_factory(app, request, uuid)

    @app_class.path(model=APIKeyCollection,
                    path='%s/%s/' % (
                        basepath, apikeypath))
    def _apikey_collection_factory(app, request):
        return apikey_collection_factory(app, request)

    @app_class.path(model=GroupModel,
                    path='%s/%s/{identifier}' % (basepath, grouppath))
    def _group_model_factory(app, request, identifier):
        return group_model_factory(request, identifier)

    @app_class.path(model=GroupCollection,
                    path='%s/%s' % (basepath, grouppath))
    def _group_collection_factory(app, request):
        return group_collection_factory(request)
