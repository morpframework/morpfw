from ...app import BaseApp
from .apikey.model import APIKeyCollection, APIKeyModel, APIKeySchema
from .apikey.path import get_apikey, get_apikey_collection
from .group.model import GroupCollection, GroupModel, GroupSchema
from .group.path import get_group, get_group_collection
from .user.model import CurrentUserModel, UserCollection, UserModel
from .user.path import get_user, get_user_collection


def hook_auth_models(cls, prefix=""):
    @cls.path(
        model=UserModel,
        path="%s/user/{username}" % prefix,
        variables=lambda obj: {"username": obj.data["username"]},
    )
    def _get_user(app, request, username):
        return get_user_collection(request).get_by_username(username)

    @cls.path(model=UserCollection, path="%s/user" % prefix)
    def _get_user_collection(app, request):
        return get_user_collection(request)

    @cls.path(model=CurrentUserModel, path="%s/self" % prefix)
    def _get_current_user(app, request):
        userid = request.identity.userid
        if not userid:
            return None
        col = get_user_collection(request)
        user = col.get_by_userid(userid)
        if not user:
            return None
        return CurrentUserModel(request, user.collection, user.data.data)

    @cls.path(model=GroupModel, path="%s/group/{identifier}" % prefix)
    def _get_group(app, request, identifier):
        return get_group_collection(request).get_by_groupname(identifier)

    @cls.path(model=GroupCollection, path="%s/group" % prefix)
    def _get_group_collection(app, request):
        return get_group_collection(request)

    @cls.path(model=APIKeyModel, path="%s/apikey/{uuid}" % prefix)
    def _get_apikey(app, request, uuid):
        return get_apikey(request, uuid)

    @cls.path(model=APIKeyCollection, path="%s/apikey" % prefix)
    def _get_apikey_collection(app, request):
        return get_apikey_collection(request)


BaseApp.hook_auth_models = classmethod(hook_auth_models)
