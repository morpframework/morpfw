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

    authn_storage = dectate.directive(action.StorageAction)

    def get_authn_storage(self, request: morepath.Request, schema: Type[morpfw.Schema]):
        name = request.app.settings.application.authn_storage
        storage_opts = request.app.settings.application.authn_storage_opts
        return self._get_authn_storage(name, schema)(request=request,
                                                     **storage_opts)

    @reg.dispatch_method(reg.match_key('name',
                                       lambda self, name, schema: name),
                         reg.match_class('schema',
                                         lambda self, name, schema: schema))
    def _get_authn_storage(self, name, schema):
        raise NotImplementedError

    def get_roles(self, request: morepath.Request, username: Optional[str] = None,
                  groupname: str = '__default__'):
        if username is None:
            username = request.identity.userid
        from .group.model import GroupSchema
        storage = self.get_authn_storage(request, GroupSchema)
        return storage.get_group_user_roles(groupname, username)

    def has_role(self, request: morepath.Request, rolename: str,
                 username: Optional[str] = None,
                 groupname: str = '__default__'):
        return rolename in self.get_roles(request, username, groupname)

    def __repr__(self):
        return u'AuthManager'
