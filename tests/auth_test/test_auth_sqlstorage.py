import yaml
import os
from test_auth import _test_authentication, get_client
from more.jwtauth import JWTIdentityPolicy
from morpfw.auth.app import App
from more.transaction import TransactionApp
from morepath.reify import reify
from morepath.request import Request
from morpfw.app import SQLApp


class SQLStorageApp(SQLApp):
    pass


def test_authentication_sqlstorage(pgsql_db):
    with open(os.path.join(os.path.dirname(__file__),
                           'settings-sqlalchemy.yml')) as f:
        settings = yaml.load(f)

    c = get_client(SQLStorageApp, settings)

    _test_authentication(c)
