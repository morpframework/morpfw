import dectate
import reg
import celery
from uuid import uuid4


class StorageAction(dectate.Action):

    app_class_arg = True

    def __init__(self, schema):
        self.schema = schema

    def identifier(self, app_class):
        return str((self.schema))

    def perform(self, obj, app_class):
        app_class._get_authn_storage.register(
            reg.methodify(obj), schema=self.schema)


class AuthnProviderAction(dectate.Action):

    app_class_arg = True

    def identifier(self, app_class):
        return str((app_class, uuid4().hex))

    def perform(self, obj, app_class):
        app_class.get_authn_provider.register(reg.methodify(obj))
