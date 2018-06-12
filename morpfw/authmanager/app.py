import morepath
from more.jwtauth import JWTIdentityPolicy
from ..jslcrud import App as CRUDApp
import reg
import dectate
from . import action
from morepath.reify import reify
import json

_REGISTERED_APPS = []


class App(CRUDApp):

    authmanager_storage = dectate.directive(action.StorageAction)

    def __repr__(self):
        return u'AuthManager'

    def get_authmanager_storage(self, request, schema):
        name = self.settings.authmanager.storage
        storage_opts = getattr(self.settings.authmanager, 'storage_opts', {})
        return self._get_authmanager_storage(name, schema)(request=request,
                                                           **storage_opts)

    @reg.dispatch_method(reg.match_key('name',
                                       lambda self, name, schema: name),
                         reg.match_class('schema',
                                         lambda self, name, schema: schema))
    def _get_authmanager_storage(self, name, schema):
        raise NotImplementedError

    def authmanager_has_role(self, request, rolename,
                             username=None,  groupname='__default__'):
        if username is None:
            username = request.identity.userid
        from .model.group import GroupSchema
        storage = self.get_authmanager_storage(request, GroupSchema)
        return rolename in storage.get_group_user_roles(groupname, username)

    def authmanager_permits(self, request, context, permission):
        identity = request.identity
        return request.app._permits(identity, context, permission)

    @classmethod
    def authmanager_register(klass, basepath='api/v1',
                             userpath='user', grouppath='group'):

        if klass in _REGISTERED_APPS:
            return

        from .path import register_authmanager
        register_authmanager(app_class=klass,
                             basepath=basepath,
                             userpath=userpath,
                             grouppath=grouppath)

        _REGISTERED_APPS.append(klass)
