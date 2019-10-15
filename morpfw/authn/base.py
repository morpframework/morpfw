import abc
import morepath
from typing import Optional, Type


class AuthnPolicy(abc.ABC):

    app_cls: Optional[Type[morepath.App]] = None

    def __init__(self, policy_settings):
        self.policy_settings = policy_settings
        super().__init__()

    @abc.abstractmethod
    def get_identity_policy(self, settings):
        raise NotImplementedError

    @abc.abstractmethod
    def verify_identity(self, app, identity):
        raise NotImplementedError
