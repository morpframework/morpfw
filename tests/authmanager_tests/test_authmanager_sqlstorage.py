import yaml
import os
from test_authmanager import _test_authentication, get_client
from more.jwtauth import JWTIdentityPolicy
from morpfw.authmanager.app import App
from more.transaction import TransactionApp
from morepath.reify import reify
from morepath.request import Request
from morpfw.authmanager import Session


class DBSessionRequest(Request):

    @reify
    def db_session(self):
        return Session()


class SQLStorageApp(TransactionApp, App):

    request_class = DBSessionRequest


SQLStorageApp.authmanager_register()


def test_authentication_sqlstorage(pgsql_db):
    with open(os.path.join(os.path.dirname(__file__),
                           'settings-sqlalchemy.yml')) as f:
        settings = yaml.load(f)

    c = get_client(SQLStorageApp, settings)

    _test_authentication(c)
