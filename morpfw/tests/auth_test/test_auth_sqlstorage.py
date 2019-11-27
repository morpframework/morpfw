import yaml
import os
from .test_auth import _test_authentication
from ..common import get_client, create_admin
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
    config = os.path.join(os.path.dirname(__file__), 'settings-sqlalchemy.yml')

    c = get_client(config)
    create_admin(c, 'admin', 'password', 'admin@localhost.localdomain')
    _test_authentication(c)
