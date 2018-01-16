from .app import App
from .model.user import UserCollection, UserModel, UserSchema
from .model.group import GroupModel, GroupCollection, GroupSchema
from .model.apikey import APIKeyCollection, APIKeyModel, APIKeySchema


def user_factory(app, request, identifier):
    collection = user_collection_factory(app, request)
    return collection.get(identifier)


def user_collection_factory(app, request):
    return UserCollection(request,
                          app.get_authmanager_storage(request, UserSchema))


def apikey_collection_factory(app, request):
    return APIKeyCollection(request,
                            app.get_authmanager_storage(request, APIKeySchema))


def apikey_factory(app, request, identifier):
    collection = apikey_collection_factory(app, request)
    return collection.get(identifier)


def group_model_factory(app, request, identifier):
    storage = app.get_authmanager_storage(request, GroupSchema)
    return storage.get(identifier)


def group_collection_factory(app, request):
    return GroupCollection(request,
                           app.get_authmanager_storage(request, GroupSchema))


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
        return user_factory(app, request, username)

    @app_class.path(model=UserCollection,
                    path='%s/%s' % (basepath, userpath))
    def _user_collection_factory(app, request):
        return user_collection_factory(app, request)

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
        return group_model_factory(app, request, identifier)

    @app_class.path(model=GroupCollection,
                    path='%s/%s' % (basepath, grouppath))
    def _group_collection_factory(app, request):
        return group_collection_factory(app, request)
