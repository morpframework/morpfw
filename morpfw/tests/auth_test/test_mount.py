import morpfw
from morpfw import sql as morpsql
from morpfw.app import BaseApp
from morpfw.crud.schema import Schema
from morpfw.authn.pas.app import App as AuthApp
from morpfw.authn.pas.user.path import get_user_collection
import sqlalchemy as sa
import jsl
from .test_auth import get_client
import morepath


class App(morpfw.SQLApp):
    pass


class MountedApp(AuthApp, morpfw.SQLApp):
    pass


class AppRoot(object):
    pass


@App.mount(app=MountedApp, path='/api/v1')
def mount_app(app):
    return MountedApp()


@App.json(model=AppRoot, name='login', request_method='POST')
def login(context, request):
    newreq = request.copy(app=MountedApp())
    coll = get_user_collection(newreq)
    data = newreq.json
    return {
        'authenticated': True if coll.authenticate(**data) else False
    }


@App.path(model=AppRoot, path='/')
def get_root():
    return AppRoot()


def test_morp_framework(pgsql_db):
    c = get_client(App, config='settings-mount.yml')

    r = c.post_json(
        '/api/v1/user/+login', {'username': 'admin',
                                'password': 'password'})

    c.authorization = ('JWT', r.headers.get('Authorization').split()[1])

    r = c.get('/api/v1/user/+refresh_token')

    c.authorization = ('JWT', r.headers.get('Authorization').split()[1])

    r = c.post_json('/+login', {'username': 'admin', 'password': 'password'})
    assert r.json['authenticated'] == True

    r = c.post_json('/+login', {'username': 'admin', 'password': 'invalid'})
    assert r.json['authenticated'] == False
