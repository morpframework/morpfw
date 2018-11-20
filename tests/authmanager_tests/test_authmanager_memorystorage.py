from test_authmanager import _test_authentication, get_client
from more.jwtauth import JWTIdentityPolicy
from morpfw.app import BaseApp


class MemoryStorageApp(BaseApp):
    pass


def test_authentication_memorystorage():
    c = get_client(MemoryStorageApp)
    _test_authentication(c)
