from more.jwtauth import JWTIdentityPolicy
from morepath import Identity, NO_IDENTITY
import rulez
from ..path import get_apikey_collection
from .base import AuthnPolicy as BaseAuthnPolicy


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


class AuthnPolicy(BaseAuthnPolicy):

    @classmethod
    def get_identity_policy(cls, settings):
        jwtauth_settings = settings.jwtauth
        if jwtauth_settings:
            # Pass the settings dictionary to the identity policy.
            return JWTWithAPIKeyIdentityPolicy(**jwtauth_settings.__dict__.copy())
        raise Exception('JWTAuth configuration is not set')

    @classmethod
    def verify_identity(cls, app, identity):
        return True
