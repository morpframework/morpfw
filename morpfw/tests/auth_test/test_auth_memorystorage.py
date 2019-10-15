from .test_auth import _test_authentication, get_client
from more.jwtauth import JWTIdentityPolicy
from morpfw.app import BaseApp
from morpfw.authn.pas.app import App
import os
import yaml
from morpfw.authn.pas.policy import MemoryStorageAuthnPolicy
from morpfw.authn.pas.policy import MemoryStorageAuthApp as BaseAuthApp
from morpfw.authz.pas import DefaultAuthzPolicy


class MemoryStorageApp(BaseAuthApp, DefaultAuthzPolicy):
    pass


class AuthnPolicy(MemoryStorageAuthnPolicy):
    pass


def test_authentication_memorystorage():
    with open(os.path.join(os.path.dirname(__file__),
                           'settings-memorystorage.yml')) as f:
        settings = yaml.load(f)

    c = get_client(MemoryStorageApp, settings)
    _test_authentication(c)
