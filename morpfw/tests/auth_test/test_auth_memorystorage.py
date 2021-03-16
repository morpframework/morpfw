import os

import yaml
from more.jwtauth import JWTIdentityPolicy
from morpfw.app import BaseApp
from morpfw.authn.pas.app import App
from morpfw.authn.pas.path import hook_auth_models
from morpfw.authn.pas.policy import MemoryStorageAuthApp as BaseAuthApp
from morpfw.authz.pas import DefaultAuthzPolicy

from ..common import create_admin, get_client
from .test_auth import _test_authentication


class MemoryStorageApp(BaseAuthApp, DefaultAuthzPolicy):
    pass


MemoryStorageApp.hook_auth_models()
MemoryStorageApp.hook_oauth_models()


def test_authentication_memorystorage():
    config = os.path.join(os.path.dirname(__file__), "settings-memorystorage.yml")
    c = get_client(config)
    create_admin(c.mfw_request, "admin", "password", "admin@localhost.localdomain")
    _test_authentication(c)
