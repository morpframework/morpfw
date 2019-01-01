from more.jwtauth import JWTIdentityPolicy
from morepath import Identity, NO_IDENTITY
import rulez
from .path import get_apikey_collection
from ..base import AuthnPolicy as BaseAuthnPolicy
from ...app import SQLApp
from .app import App as BaseAuthApp
from .user.model import UserSchema
from .group.model import GroupSchema
from .apikey.model import APIKeySchema
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


@SQLStorageAuthApp.authn_storage(schema=UserSchema)
def get_user_sqlstorage_factory(schema):
    return UserSQLStorage


@SQLStorageAuthApp.authn_storage(schema=GroupSchema)
def get_group_sqlstorage_factory(schema):
    return GroupSQLStorage


@SQLStorageAuthApp.authn_storage(schema=APIKeySchema)
def get_apikey_sqlstorage_factory(schema):
    return APIKeySQLStorage


class SQLStorageAuthnPolicy(DefaultAuthnPolicy):

    app_cls = SQLStorageAuthApp


class MemoryStorageAuthApp(BaseAuthApp):
    pass


@MemoryStorageAuthApp.authn_storage(schema=UserSchema)
def get_user_memorystorage_factory(schema):
    return UserMemoryStorage


@MemoryStorageAuthApp.authn_storage(schema=GroupSchema)
def get_group_memorystorage_factory(schema):
    return GroupMemoryStorage


@MemoryStorageAuthApp.authn_storage(schema=APIKeySchema)
def get_apikey_memorystorage_factory(schema):
    return APIKeyMemoryStorage


class MemoryStorageAuthnPolicy(DefaultAuthnPolicy):

    app_cls = MemoryStorageAuthApp
