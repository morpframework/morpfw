from more.itsdangerous import IdentityPolicy
from .base import AuthnPolicy as BaseAuthnPolicy


class AuthnPolicy(BaseAuthnPolicy):

    def get_identity_policy(self, settings):
        if settings.application.development_mode:
            secure = False
        else:
            secure = True
        return IdentityPolicy(secure=secure)

    def verify_identity(self, app, identity):
        return True
