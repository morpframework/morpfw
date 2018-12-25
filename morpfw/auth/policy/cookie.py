from more.itsdangerous import IdentityPolicy
from .base import AuthnPolicy as BaseAuthnPolicy


class AuthnPolicy(BaseAuthnPolicy):

    @classmethod
    def get_identity_policy(cls, settings):
        if settings.application.development_mode:
            secure = False
        else:
            secure = True
        return IdentityPolicy(secure=secure)

    @classmethod
    def verify_identity(cls, app, identity):
        return True
