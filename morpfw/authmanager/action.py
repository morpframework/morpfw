import dectate
import reg


class StorageAction(dectate.Action):

    app_class_arg = True

    def __init__(self, name, schema):
        self.name = name
        self.schema = schema

    def identifier(self, app_class):
        return str((self.name, self.schema))

    def perform(self, obj, app_class):
        app_class._get_authmanager_storage.register(
            reg.methodify(obj), name=self.name, schema=self.schema)
