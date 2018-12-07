import dectate
import reg
import celery
from uuid import uuid4


class AuthnzProviderAction(dectate.Action):

    app_class_arg = True

    def identifier(self, app_class):
        return str((app_class, uuid4().hex))

    def perform(self, obj, app_class):
        app_class.get_authnz_provider.register(reg.methodify(obj))
