from morepath import Identity, NO_IDENTITY
from .base import AuthnPolicy as BaseAuthnPolicy
from ipaddress import IPv4Address, IPv4Network


class NoAuthIdentityPolicy(object):

    def identify(self, request):
        return Identity('ANONYMOUS')

    def remember(self, response, request, identity):
        pass

    def forget(self, response, request):
        pass


class AuthnPolicy(BaseAuthnPolicy):

    @classmethod
    def get_identity_policy(cls, settings):
        return NoAuthIdentityPolicy()

    @classmethod
    def verify_identity(cls, app, identity):
        return True
