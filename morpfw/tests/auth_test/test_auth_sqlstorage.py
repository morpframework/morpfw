import os

import yaml
from more.jwtauth import JWTIdentityPolicy
from more.transaction import TransactionApp
from morepath.reify import reify
from morepath.request import Request
from morpfw.app import SQLApp
from morpfw.authn.pas.app import App
from morpfw.authn.pas.path import hook_auth_models
from morpfw.authz.pas import DefaultAuthzPolicy
from morpfw.sql import Base

from ..common import create_admin, get_client
from .test_auth import _test_authentication


class SQLStorageApp(SQLApp, DefaultAuthzPolicy):
    pass


SQLStorageApp.hook_auth_models()
SQLStorageApp.hook_oauth_models()


def test_authentication_sqlstorage(pgsql_db):
    config = os.path.join(os.path.dirname(__file__), "settings-sqlalchemy.yml")

    c = get_client(config)
    req = c.mfw_request
    Base.metadata.create_all(bind=req.db_session.bind)
    create_admin(c.mfw_request, "admin", "password", "admin@localhost.localdomain")
    _test_authentication(c)
