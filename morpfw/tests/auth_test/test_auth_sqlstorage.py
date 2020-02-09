import os

import yaml
from more.jwtauth import JWTIdentityPolicy
from more.transaction import TransactionApp
from morepath.reify import reify
from morepath.request import Request
from morpfw.app import SQLApp
from morpfw.authn.pas.app import App
from morpfw.authn.pas.path import hook_auth_models
from morpfw.authn.pas.policy import SQLStorageAuthApp as BaseAuthApp
from morpfw.authn.pas.policy import SQLStorageAuthnPolicy
from morpfw.authz.pas import DefaultAuthzPolicy
from morpfw.sql import Base

from ..common import create_admin, get_client, make_request
from .test_auth import _test_authentication


class SQLStorageApp(SQLApp, DefaultAuthzPolicy):
    pass


class AuthnPolicy(SQLStorageAuthnPolicy):
    pass


SQLStorageApp.hook_auth_models()


def test_authentication_sqlstorage(pgsql_db):
    config = os.path.join(os.path.dirname(__file__), "settings-sqlalchemy.yml")

    c = get_client(config)
    req = make_request(c.app)
    Base.metadata.create_all(bind=req.db_session.bind)
    create_admin(c, "admin", "password", "admin@localhost.localdomain")
    _test_authentication(c)
