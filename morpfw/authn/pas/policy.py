from more.jwtauth import JWTIdentityPolicy
from morepath import Identity, NO_IDENTITY
import rulez
from .path import get_apikey_collection
from ..base import AuthnPolicy as BaseAuthnPolicy
from ...app import SQLApp
from .app import App as BaseAuthApp
from .user.model import UserSchema, UserModel
from .group.model import GroupSchema, GroupModel
from .apikey.model import APIKeySchema, APIKeyModel
from .storage.sqlstorage.sqlstorage import GroupSQLStorage, UserSQLStorage, APIKeySQLStorage
from .storage.memorystorage import GroupMemoryStorage, UserMemoryStorage, APIKeyMemoryStorage


class JWTWithAPIKeyIdentityPolicy(JWTIdentityPolicy):

    def identify(self, request):
        api_key = request.headers.get('X-API-KEY', None)
        if api_key:
            api_identity, api_secret = api_key.split('.')
            apikeys = get_apikey_collection(request)
            keys = apikeys.search(
                rulez.field['api_identity'] == api_identity, secure=False)
            if keys and keys[0].data['api_secret'] == api_secret:
                userid = keys[0].data['userid']
                return Identity(userid=userid)
        return super(JWTWithAPIKeyIdentityPolicy, self).identify(request)


class DefaultAuthnPolicy(BaseAuthnPolicy):

    def get_identity_policy(self, settings):
        jwtauth_settings = settings.jwtauth
        if jwtauth_settings:
            # Pass the settings dictionary to the identity policy.
            return JWTWithAPIKeyIdentityPolicy(**jwtauth_settings.__dict__.copy())
        raise Exception('JWTAuth configuration is not set')

    def verify_identity(self, app, identity):
        return True


class SQLStorageAuthApp(BaseAuthApp, SQLApp):
    pass


@SQLStorageAuthApp.storage(model=UserModel)
def get_user_sqlstorage(model, request, blobstorage):
    return UserSQLStorage(request, blobstorage=blobstorage)


@SQLStorageAuthApp.storage(model=GroupModel)
def get_group_sqlstorage(model, request, blobstorage):
    return GroupSQLStorage(request, blobstorage=blobstorage)


@SQLStorageAuthApp.storage(model=APIKeyModel)
def get_apikey_sqlstorage(model, request, blobstorage):
    return APIKeySQLStorage(request, blobstorage=blobstorage)


class SQLStorageAuthnPolicy(DefaultAuthnPolicy):

    app_cls = SQLStorageAuthApp


class MemoryStorageAuthApp(BaseAuthApp):
    pass


@MemoryStorageAuthApp.storage(model=UserModel)
def get_user_memorystorage(model, request, blobstorage):
    return UserMemoryStorage(request, blobstorage=blobstorage)


@MemoryStorageAuthApp.storage(model=GroupModel)
def get_group_memorystorage(model, request, blobstorage):
    return GroupMemoryStorage(request, blobstorage=blobstorage)


@MemoryStorageAuthApp.storage(model=APIKeyModel)
def get_apikey_memorystorage(model, request, blobstorage):
    return APIKeyMemoryStorage(request, blobstorage=blobstorage)


class MemoryStorageAuthnPolicy(DefaultAuthnPolicy):

    app_cls = MemoryStorageAuthApp
