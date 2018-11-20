import morepath
from more.jwtauth import JWTIdentityPolicy
from morpfw.crud import App as CRUDApp
import reg
import dectate
from . import action
from morepath.reify import reify
import json
from typing import List, Optional, Type
import morpfw

_REGISTERED_APPS: List[morepath.App] = []


class App(CRUDApp):

    authmanager_storage = dectate.directive(action.StorageAction)

    def __repr__(self):
        return u'AuthManager'

    def get_authmanager_storage(self, request: morepath.Request, schema: Type[morpfw.Schema]):
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

    def authmanager_has_role(self, request: morepath.Request, rolename: str,
                             username: Optional[str] = None, groupname: str = '__default__'):
        if username is None:
            username = request.identity.userid
        from .group.model import GroupSchema
        storage = self.get_authmanager_storage(request, GroupSchema)
        return rolename in storage.get_group_user_roles(groupname, username)

    def authmanager_permits(self, request: morepath.Request, context: morpfw.Model, permission: str):
        identity = request.identity
        return request.app._permits(identity, context, permission)
