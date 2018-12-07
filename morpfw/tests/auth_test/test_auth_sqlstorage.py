import yaml
import os
from .test_auth import _test_authentication, get_client
from more.jwtauth import JWTIdentityPolicy
from more.transaction import TransactionApp
from morepath.reify import reify
from morepath.request import Request
from morpfw.app import SQLApp
from morpfw.auth.app import App


class SQLStorageAuthApp(App, SQLApp):
    pass


class SQLStorageApp(SQLApp):
    pass


@SQLStorageApp.mount(app=SQLStorageAuthApp, path='/auth')
def mount_app(app):
    return SQLStorageAuthApp()


def test_authentication_sqlstorage(pgsql_db):
    with open(os.path.join(os.path.dirname(__file__),
                           'settings-sqlalchemy.yml')) as f:
        settings = yaml.load(f)

    c = get_client(SQLStorageApp, settings)

    _test_authentication(c)
