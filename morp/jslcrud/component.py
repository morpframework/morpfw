import dectate
import reg
from . import signals


class DataProviderAction(dectate.Action):

    app_class_arg = True

    def __init__(self, schema, obj, storage):
        self.schema = schema
        self.obj = obj
        self.storage = storage

    def identifier(self, app_class):
        return str((app_class, self.schema, self.obj, self.storage))

    def perform(self, obj, app_class):
        app_class.get_jslcrud_dataprovider.register(reg.methodify(obj),
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
        app_class.get_jslcrud_jsonprovider.register(
            reg.methodify(obj), obj=self.obj)


class JSONTransformAction(dectate.Action):

    app_class_arg = True

    def __init__(self, schema):
        self.schema = schema

    def identifier(self, app_class):
        return str((app_class, self.schema))

    def perform(self, obj, app_class):
        app_class.get_jslcrud_jsontransform.register(
            reg.methodify(lambda schema: obj), schema=self.schema)


class IdentifierFieldsAction(dectate.Action):

    app_class_arg = True

    def __init__(self, schema):
        self.schema = schema

    def identifier(self, app_class):
        return str((app_class, self.schema))

    def perform(self, obj, app_class):
        app_class.get_jslcrud_identifierfields.register(
            reg.methodify(obj), schema=self.schema)


class UUIDFieldAction(dectate.Action):

    app_class_arg = True

    def __init__(self, schema):
        self.schema = schema

    def identifier(self, app_class):
        return str((app_class, self.schema))

    def perform(self, obj, app_class):
        app_class.get_jslcrud_uuidfield.register(
            reg.methodify(obj), schema=self.schema)


class DefaultIdentifierAction(dectate.Action):

    app_class_arg = True

    def __init__(self, schema):
        self.schema = schema

    def identifier(self, app_class):
        return str((app_class, self.schema))

    def perform(self, obj, app_class):
        app_class.get_jslcrud_default_identifier.register(
            reg.methodify(obj), schema=self.schema)


class FormValidatorAction(dectate.Action):

    app_class_arg = True

    def __init__(self, schema):
        self.schema = schema

    def identifier(self, app_class):
        return str((app_class, self.schema))

    def perform(self, obj, app_class):
        app_class.get_jslcrud_formvalidators.register(
            reg.methodify(obj), schema=self.schema)


class RulesAdapterAction(dectate.Action):

    app_class_arg = True

    def __init__(self, model):
        self.model = model

    def identifier(self, app_class):
        return str((app_class, self.model))

    def perform(self, obj, app_class):
        app_class._jslcrud_rulesadapter.register(
            reg.methodify(obj), model=self.model)


class StateMachineAction(dectate.Action):

    app_class_arg = True

    def __init__(self, model):
        self.model = model

    def identifier(self, app_class):
        return str((app_class, self.model))

    def perform(self, obj, app_class):
        app_class._jslcrud_statemachine.register(
            reg.methodify(obj), model=self.model)
