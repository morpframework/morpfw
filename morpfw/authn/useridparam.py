from morepath import NO_IDENTITY
from ..identity import Identity
from .base import AuthnPolicy as BaseAuthnPolicy
from ipaddress import IPv4Address, IPv4Network


class UserParamIdentityPolicy(object):

    def __init__(self, allowed_nets=None):
        self.allowed_nets = []
        for n in (allowed_nets or []):
            self.allowed_nets.append(IPv4Network(n))

    def identify(self, request):
        userid = request.GET.get('user.id', None)
        if userid:
            remote_addr = IPv4Address(request.remote_addr)
            for n in self.allowed_nets:
                if remote_addr in n:
                    return Identity(userid)
        return NO_IDENTITY

    def remember(self, response, request, identity):
        pass

    def forget(self, response, request):
        pass


class AuthnPolicy(BaseAuthnPolicy):

    @classmethod
    def get_identity_policy(cls, settings):
        return UserParamIdentityPolicy(allowed_nets=settings.security.allowed_nets)

    @classmethod
    def verify_identity(cls, app, identity):
        return True
