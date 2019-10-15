import yaml
import os
from .test_auth import _test_authentication, get_client
from more.jwtauth import JWTIdentityPolicy
from more.transaction import TransactionApp
from morepath.reify import reify
from morepath.request import Request
from morpfw.app import SQLApp
from morpfw.authn.pas.app import App
from morpfw.authn.pas.policy import SQLStorageAuthnPolicy
from morpfw.authn.pas.policy import SQLStorageAuthApp as BaseAuthApp
from morpfw.authz.pas import DefaultAuthzPolicy
from morpfw.authn.pas.path import hook_auth_models


class SQLStorageApp(SQLApp, DefaultAuthzPolicy):
    pass


class AuthnPolicy(SQLStorageAuthnPolicy):
    pass


SQLStorageApp.hook_auth_models()


def test_authentication_sqlstorage(pgsql_db):
    with open(os.path.join(os.path.dirname(__file__),
                           'settings-sqlalchemy.yml')) as f:
        settings = yaml.load(f)

    c = get_client(SQLStorageApp, settings)

    _test_authentication(c)
