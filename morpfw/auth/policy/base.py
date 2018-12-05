
class AuthnPolicy(object):

    @classmethod
    def get_identity_policy(cls, settings):
        raise NotImplementedError

    @classmethod
    def verify_identity(cls, app, identity):
        raise NotImplementedError
