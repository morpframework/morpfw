import morpfw
from morpfw import sql as morpsql
from morpfw.app import BaseApp
from morpfw.crud.model import Schema
import sqlalchemy as sa
import jsl
from test_auth import get_client
import jsonobject
import morepath


class App(morpfw.SQLApp):
    pass


class MountedApp(morpfw.SQLApp):
    pass


@App.mount(app=MountedApp, path='/api/v1')
def mount_app(app):
    return MountedApp()


def test_morp_framework(pgsql_db):
    c = get_client(App, config='settings-mount.yml')

    r = c.post_json(
        '/api/v1/user/+login', {'username': 'admin',
                                'password': 'password'})

    c.authorization = ('JWT', r.headers.get('Authorization').split()[1])

    r = c.get('/user/+refresh_token')

    c.authorization = ('JWT', r.headers.get('Authorization').split()[1])
