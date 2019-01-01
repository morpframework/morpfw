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
from ..app import BaseApp

_REGISTERED_APPS: List[morepath.App] = []


class App(BaseApp):

    authn_storage = dectate.directive(action.StorageAction)

    def get_authn_storage(self, request: morepath.Request, schema: Type[morpfw.Schema]):
        return self._get_authn_storage(schema)(request=request)

    @reg.dispatch_method(reg.match_class('schema',
                                         lambda self, schema: schema))
    def _get_authn_storage(self, schema):
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
