from .test_auth import _test_authentication
from ..common import get_client, create_admin
from more.jwtauth import JWTIdentityPolicy
from morpfw.app import BaseApp
from morpfw.authn.pas.app import App
from morpfw.authn.pas.path import hook_auth_models
import os
import yaml
from morpfw.authn.pas.policy import MemoryStorageAuthnPolicy
from morpfw.authn.pas.policy import MemoryStorageAuthApp as BaseAuthApp
from morpfw.authz.pas import DefaultAuthzPolicy


class MemoryStorageApp(BaseAuthApp, DefaultAuthzPolicy):
    pass


class AuthnPolicy(MemoryStorageAuthnPolicy):
    pass


MemoryStorageApp.hook_auth_models()


def test_authentication_memorystorage():
    config = os.path.join(os.path.dirname(__file__),
                          'settings-memorystorage.yml')
    c = get_client(config)
    create_admin(c, 'admin', 'password', 'admin@localhost.localdomain')
    _test_authentication(c)
