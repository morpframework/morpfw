import typing

import dectate
import morepath
import reg
from morepath.directive import SettingAction

from . import signals
from .blobstorage.base import BlobStorage
from .typeregistry import TypeRegistry


class StorageAction(dectate.Action):

    app_class_arg = True

    def __init__(self, model):
        self.model = model

    def identifier(self, app_class):
        return str((self.model))

    def perform(self, obj, app_class):
        app_class._get_storage.register(
            reg.methodify(obj),
            model=self.model,
            request=morepath.Request,
            blobstorage=BlobStorage,
        )


class BlobStorageAction(dectate.Action):

    app_class_arg = True

    def __init__(self, model):
        self.model = model

    def identifier(self, app_class):
        return str((self.model))

    def perform(self, obj, app_class):
        app_class._get_blobstorage.register(
            reg.methodify(obj), model=self.model, request=morepath.Request
        )


class DataProviderAction(dectate.Action):

    app_class_arg = True

    def __init__(self, schema, obj, storage):
        self.schema = schema
        self.obj = obj
        self.storage = storage

    def identifier(self, app_class):
        return (self.schema, self.obj, self.storage)

    def perform(self, obj, app_class):
        app_class.get_dataprovider.register(
            reg.methodify(obj), schema=self.schema, obj=self.obj, storage=self.storage
        )


class JSONProviderAction(dectate.Action):

    app_class_arg = True

    def __init__(self, obj):
        self.obj = obj

    def identifier(self, app_class):
        return (self.obj,)

    def perform(self, obj, app_class):
        app_class.get_jsonprovider.register(reg.methodify(obj), obj=self.obj)


class IdentifierFieldAction(dectate.Action):

    app_class_arg = True

    def __init__(self, schema):
        self.schema = schema

    def identifier(self, app_class):
        return (self.schema,)

    def perform(self, obj, app_class):
        app_class.get_identifierfield.register(reg.methodify(obj), schema=self.schema)


class UUIDFieldAction(dectate.Action):

    app_class_arg = True

    def __init__(self, schema):
        self.schema = schema

    def identifier(self, app_class):
        return (self.schema,)

    def perform(self, obj, app_class):
        app_class.get_uuidfield.register(reg.methodify(obj), schema=self.schema)


class DefaultIdentifierAction(dectate.Action):

    app_class_arg = True

    def __init__(self, schema):
        self.schema = schema

    def identifier(self, app_class):
        return (self.schema,)

    def perform(self, obj, app_class):
        app_class.get_default_identifier.register(
            reg.methodify(obj), schema=self.schema
        )


class FormValidatorAction(dectate.Action):

    app_class_arg = True

    def __init__(self, schema):
        self.schema = schema

    def identifier(self, app_class):
        return (self.schema,)

    def perform(self, obj, app_class):
        app_class.get_formvalidators.register(reg.methodify(obj), schema=self.schema)


class RulesProviderAction(dectate.Action):

    app_class_arg = True

    def __init__(self, model):
        self.model = model

    def identifier(self, app_class):
        return (self.model,)

    def perform(self, obj, app_class):
        app_class.get_rulesprovider.register(reg.methodify(obj), model=self.model)


class StateMachineAction(dectate.Action):

    app_class_arg = True

    def __init__(self, model):
        self.model = model

    def identifier(self, app_class):
        return (self.model,)

    def perform(self, obj, app_class):
        app_class.get_statemachine.register(reg.methodify(obj), model=self.model)

        def factory(model):
            return obj

        app_class.get_statemachine_factory.register(
            reg.methodify(factory), model=self.model
        )


class SearchProviderAction(dectate.Action):

    app_class_arg = True

    def __init__(self, model):
        self.model = model

    def identifier(self, app_class):
        return (self.model,)

    def perform(self, obj, app_class):
        app_class.get_searchprovider.register(reg.methodify(obj), model=self.model)


class AggregateProviderAction(dectate.Action):

    app_class_arg = True

    def __init__(self, model):
        self.model = model

    def identifier(self, app_class):
        return (self.model,)

    def perform(self, obj, app_class):
        app_class.get_aggregateprovider.register(reg.methodify(obj), model=self.model)


class XattrProviderAction(dectate.Action):

    app_class_arg = True

    def __init__(self, model):
        self.model = model

    def identifier(self, app_class):
        return (self.model,)

    def perform(self, obj, app_class):
        app_class.get_xattrprovider.register(reg.methodify(obj), model=self.model)


class TypeInfoFactoryAction(dectate.Action):

    config = {"type_registry": TypeRegistry}

    app_class_arg = True

    depends = [SettingAction]

    def __init__(self, name, schema):
        self.name = name
        self.schema = schema

    def identifier(self, app_class, type_registry: TypeRegistry):
        return self.name

    def perform(self, obj, app_class, type_registry: TypeRegistry):
        def factory(name):
            return obj

        app_class.get_typeinfo_factory.register(reg.methodify(factory), name=self.name)
        type_registry.register_type(name=self.name, schema=self.schema)


class StorageFactoryAction(dectate.Action):

    app_class_arg = True

    def __init__(self, name):
        self.name = name

    def identifier(self, app_class):
        return self.name

    def perform(self, obj, app_class):
        def factory(name):
            return obj

        app_class._get_storage_factory.register(reg.methodify(factory), name=self.name)


class BlobStorageFactoryAction(dectate.Action):

    app_class_arg = True

    def __init__(self, name):
        self.name = name

    def identifier(self, app_class):
        return self.name

    def perform(self, obj, app_class):
        def factory(name):
            return obj

        app_class._get_blobstorage_factory.register(
            reg.methodify(factory), name=self.name
        )


class MetalinkAction(dectate.Action):

    app_class_arg = True

    def __init__(self, name, model):
        self.name = name
        self.model = model

    def identifier(self, app_class):
        return self.name

    def perform(self, obj, app_class):
        def name_factory(name, request):
            return obj(request)

        app_class._get_metalinkprovider_by_name.register(
            reg.methodify(name_factory), name=self.name
        )

        def model_factory(model, request):
            return obj(request)

        app_class._get_metalinkprovider_by_model.register(
            reg.methodify(model_factory), model=self.model
        )


class AuthzRuleAction(dectate.Action):

    app_class_arg = True

    def __init__(self, name):
        self.name = name

    def identifier(self, app_class):
        return self.name

    def perform(self, obj, app_class):
        def factory(name):
            return obj

        app_class.get_authz_rule.register(reg.methodify(factory), name=self.name)

