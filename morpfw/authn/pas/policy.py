import morepath
import pytz
import rulez
from more.jwtauth import JWTIdentityPolicy
from morepath import NO_IDENTITY

from ...app import SQLApp
from ...identity import Identity as BaseIdentity
from ..base import AuthnPolicy as BaseAuthnPolicy
from .apikey.model import APIKeyModel, APIKeySchema
from .app import App as BaseAuthApp
from .group.model import GroupModel, GroupSchema
from .path import get_apikey_collection, get_user_collection
from .storage.memorystorage import (
    APIKeyMemoryStorage,
    GroupMemoryStorage,
    UserMemoryStorage,
)
from .storage.sqlstorage.sqlstorage import (
    APIKeySQLStorage,
    GroupSQLStorage,
    UserSQLStorage,
)
from .user.model import UserModel, UserSchema


class Identity(BaseIdentity):
    def timezone(self):
        userid = self.userid
        collection = get_user_collection(self.request)
        user = collection.get_by_userid(userid)
        if user:
            return user.timezone()
        return pytz.UTC


class JWTWithAPIKeyIdentityPolicy(JWTIdentityPolicy):
    def identify(self, request):
        api_key = request.headers.get("X-API-KEY", None)
        if api_key:
            api_identity, api_secret = api_key.split(".")
            apikeys = get_apikey_collection(request)
            keys = apikeys.search(
                rulez.field["api_identity"] == api_identity, secure=False
            )
            if keys and keys[0].data["api_secret"] == api_secret:
                userid = keys[0].data["userid"]
                return Identity(request=request, userid=userid)
        identity = super(JWTWithAPIKeyIdentityPolicy, self).identify(request)
        if isinstance(identity, morepath.Identity):
            return Identity(request=request, userid=identity.userid)
        return identity


def verify_refresh_request(request):
    jwtauth_settings = request.app.settings.configuration.__dict__[
        "morpfw.security.jwt"
    ].copy()
    jwtauth_settings["auth_header_prefix"] = "Bearer"
    identity_policy = JWTWithAPIKeyIdentityPolicy(**jwtauth_settings)
    return identity_policy.verify_refresh(request)


class DefaultAuthnPolicy(BaseAuthnPolicy):
    def get_identity_policy(self, settings):
        jwtauth_settings = settings.configuration.__dict__["morpfw.security.jwt"]
        if jwtauth_settings:
            jwtauth_settings["auth_header_prefix"] = "Bearer"
            # Pass the settings dictionary to the identity policy.
            return JWTWithAPIKeyIdentityPolicy(**jwtauth_settings)
        raise Exception("JWTAuth configuration is not set")

    def verify_identity(self, app, identity):
        return True


@SQLApp.storage(model=UserModel)
def get_user_sqlstorage(model, request, blobstorage):
    return UserSQLStorage(request, blobstorage=blobstorage)


@SQLApp.storage(model=GroupModel)
def get_group_sqlstorage(model, request, blobstorage):
    return GroupSQLStorage(request, blobstorage=blobstorage)


@SQLApp.storage(model=APIKeyModel)
def get_apikey_sqlstorage(model, request, blobstorage):
    return APIKeySQLStorage(request, blobstorage=blobstorage)


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
