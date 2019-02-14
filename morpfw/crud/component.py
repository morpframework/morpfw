import dectate
import reg
import morepath
from .blobstorage.base import BlobStorage
from . import signals
from .typeregistry import TypeRegistry
from morepath.directive import SettingAction


class StorageAction(dectate.Action):

    app_class_arg = True

    def __init__(self, model):
        self.model = model

    def identifier(self, app_class):
        return str((self.model))

    def perform(self, obj, app_class):
        app_class._get_storage.register(
            reg.methodify(obj), model=self.model,
            request=morepath.Request, blobstorage=BlobStorage)


class BlobStorageAction(dectate.Action):

    app_class_arg = True

    def __init__(self, model):
        self.model = model

    def identifier(self, app_class):
        return str((self.model))

    def perform(self, obj, app_class):
        app_class._get_blobstorage.register(
            reg.methodify(obj), model=self.model, request=morepath.Request)


class DataProviderAction(dectate.Action):

    app_class_arg = True

    def __init__(self, schema, obj, storage):
        self.schema = schema
        self.obj = obj
        self.storage = storage

    def identifier(self, app_class):
        return str((app_class, self.schema, self.obj, self.storage))

    def perform(self, obj, app_class):
        app_class.get_dataprovider.register(reg.methodify(obj),
                                            schema=self.schema,
                                            obj=self.obj,
                                            storage=self.storage)


class JSONProviderAction(dectate.Action):

    app_class_arg = True

    def __init__(self, obj):
        self.obj = obj

    def identifier(self, app_class):
        return str((app_class, self.obj))

    def perform(self, obj, app_class):
        app_class.get_jsonprovider.register(
            reg.methodify(obj), obj=self.obj)


class IdentifierFieldsAction(dectate.Action):

    app_class_arg = True

    def __init__(self, schema):
        self.schema = schema

    def identifier(self, app_class):
        return str((app_class, self.schema))

    def perform(self, obj, app_class):
        app_class.get_identifierfields.register(
            reg.methodify(obj), schema=self.schema)


class UUIDFieldAction(dectate.Action):

    app_class_arg = True

    def __init__(self, schema):
        self.schema = schema

    def identifier(self, app_class):
        return str((app_class, self.schema))

    def perform(self, obj, app_class):
        app_class.get_uuidfield.register(
            reg.methodify(obj), schema=self.schema)


class DefaultIdentifierAction(dectate.Action):

    app_class_arg = True

    def __init__(self, schema):
        self.schema = schema

    def identifier(self, app_class):
        return str((app_class, self.schema))

    def perform(self, obj, app_class):
        app_class.get_default_identifier.register(
            reg.methodify(obj), schema=self.schema)


class FormValidatorAction(dectate.Action):

    app_class_arg = True

    def __init__(self, schema):
        self.schema = schema

    def identifier(self, app_class):
        return str((app_class, self.schema))

    def perform(self, obj, app_class):
        app_class.get_formvalidators.register(
            reg.methodify(obj), schema=self.schema)


class RulesProviderAction(dectate.Action):

    app_class_arg = True

    def __init__(self, model):
        self.model = model

    def identifier(self, app_class):
        return str((app_class, self.model))

    def perform(self, obj, app_class):
        app_class.get_rulesprovider.register(
            reg.methodify(obj), model=self.model)


class StateMachineAction(dectate.Action):

    app_class_arg = True

    def __init__(self, model):
        self.model = model

    def identifier(self, app_class):
        return str((app_class, self.model))

    def perform(self, obj, app_class):
        app_class.get_statemachine.register(
            reg.methodify(obj), model=self.model)


class SearchProviderAction(dectate.Action):

    app_class_arg = True

    def __init__(self, model):
        self.model = model

    def identifier(self, app_class):
        return str((app_class, self.model))

    def perform(self, obj, app_class):
        app_class.get_searchprovider.register(
            reg.methodify(obj), model=self.model)


class AggregateProviderAction(dectate.Action):

    app_class_arg = True

    def __init__(self, model):
        self.model = model

    def identifier(self, app_class):
        return str((app_class, self.model))

    def perform(self, obj, app_class):
        app_class.get_aggregateprovider.register(
            reg.methodify(obj), model=self.model)


class XattrProviderAction(dectate.Action):

    app_class_arg = True

    def __init__(self, model):
        self.model = model

    def identifier(self, app_class):
        return str((app_class, self.model))

    def perform(self, obj, app_class):
        app_class.get_xattrprovider.register(
            reg.methodify(obj), model=self.model)


class TypeInfoFactoryAction(dectate.Action):

    config = {
        'type_registry': TypeRegistry
    }

    depends = [SettingAction]

    def __init__(self, name):
        self.name = name

    def identifier(self, type_registry: TypeRegistry):
        return self.name

    def perform(self, obj, type_registry: TypeRegistry):
        type_registry.register_typeinfo_factory(
            info_factory=obj, name=self.name)
