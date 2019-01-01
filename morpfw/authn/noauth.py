from morepath import Identity, NO_IDENTITY
from .base import AuthnPolicy as BaseAuthnPolicy


class NoAuthIdentityPolicy(object):

    def identify(self, request):
        return Identity('ANONYMOUS')

    def remember(self, response, request, identity):
        pass

    def forget(self, response, request):
        pass


class AuthnPolicy(BaseAuthnPolicy):

    def get_identity_policy(self, settings):
        return NoAuthIdentityPolicy()

    def verify_identity(self, app, identity):
        return True
