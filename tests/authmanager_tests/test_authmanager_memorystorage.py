from test_authmanager import _test_authentication, get_client
from more.jwtauth import JWTIdentityPolicy
from morp.authmanager.app import App


class MemoryStorageApp(App):
    pass


MemoryStorageApp.authmanager_register()


def test_authentication_memorystorage():
    c = get_client(MemoryStorageApp)
    _test_authentication(c)
