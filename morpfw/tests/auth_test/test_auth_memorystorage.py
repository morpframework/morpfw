from .test_auth import _test_authentication, get_client
from more.jwtauth import JWTIdentityPolicy
from morpfw.app import BaseApp
from morpfw.auth.app import App
import os
import yaml


class MemoryStorageAuthApp(App, BaseApp):
    pass


class MemoryStorageApp(BaseApp):
    pass


@MemoryStorageApp.mount(app=MemoryStorageAuthApp, path='/auth')
def mount_app(app):
    return MemoryStorageAuthApp()


def test_authentication_memorystorage():
    with open(os.path.join(os.path.dirname(__file__),
                           'settings-memorystorage.yml')) as f:
        settings = yaml.load(f)

    c = get_client(MemoryStorageApp, settings)
    _test_authentication(c)
