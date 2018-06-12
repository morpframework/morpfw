from more.jsonschema import JsonSchemaApp
from . import signals as signals
from sqlalchemy.orm import sessionmaker
import dectate
import reg
from more.signals import SignalApp
from . import component as actions
import warnings

Session = sessionmaker()


class App(JsonSchemaApp, signals.SignalApp):
    @classmethod
    def jslcrud_dataprovider(klass, *args, **kwargs):
        warnings.warn(
            "jslcrud_dataprovider is deprecated, use dataprovider", DeprecationWarning)
        return klass.dataprovider(*args, **kwargs)

    dataprovider = dectate.directive(actions.DataProviderAction)

    @classmethod
    def jslcrud_jsonprovider(klass, *args, **kwargs):
        warnings.warn(
            "jslcrud_jsonprovider is deprecated, use jsonprovider", DeprecationWarning)
        return klass.jsonprovider(*args, **kwargs)

    jsonprovider = dectate.directive(actions.JSONProviderAction)

    @classmethod
    def jslcrud_jsontransfrom(klass, *args, **kwargs):
        warnings.warn(
            "jslcrud_jsontransform is deprecated, use jsontransform", DeprecationWarning)
        return klass.jsontransform(*args, **kwargs)

    jsontransform = dectate.directive(actions.JSONTransformAction)

    @classmethod
    def jslcrud_formvalidators(klass, *args, **kwargs):
        warnings.warn(
            "jslcrud_formvalidators is deprecated, use formvalidators", DeprecationWarning)
        return klass.formvalidators(*args, **kwargs)

    formvalidators = dectate.directive(actions.FormValidatorAction)

    @classmethod
    def jslcrud_identifierfields(klass, *args, **kwargs):
        warnings.warn(
            "jslcrud_identifierfields is deprecated, use identifierfields", DeprecationWarning)
        return klass.identifierfields(*args, **kwargs)

    identifierfields = dectate.directive(actions.IdentifierFieldsAction)

    @classmethod
    def jslcrud_default_identifier(klass, *args, **kwargs):
        warnings.warn(
            "jslcrud_default_identifier is deprecated, use default_identifier", DeprecationWarning)
        return klass.default_identifier(*args, **kwargs)

    default_identifier = dectate.directive(actions.DefaultIdentifierAction)

    @classmethod
    def jslcrud_rulesadapter(klass, *args, **kwargs):
        warnings.warn(
            "jslcrud_rulesadapter is deprecated, use rulesadapter", DeprecationWarning)
        return klass.rulesadapter(*args, **kwargs)

    rulesadapter = dectate.directive(actions.RulesAdapterAction)

    @classmethod
    def jslcrud_uuidfield(klass, *args, **kwargs):
        warnings.warn(
            "jslcrud_uuidfield is deprecated, use uuidfield", DeprecationWarning)
        return klass.uuidfield(*args, **kwargs)

    uuidfield = dectate.directive(actions.UUIDFieldAction)

    @classmethod
    def jslcrud_statemachine(klass, *args, **kwargs):
        warnings.warn(
            "jslcrud_statemachine is deprecated, use statemachine", DeprecationWarning)
        return klass.statemachine(*args, **kwargs)

    statemachine = dectate.directive(actions.StateMachineAction)

    @reg.dispatch_method(
        reg.match_class('schema',
                        lambda self, schema, obj, storage: schema),
        reg.match_instance('obj'),
        reg.match_instance('storage'))
    def get_jslcrud_dataprovider(self, schema, obj, storage):
        raise NotImplementedError('Dataprovider for %s/%s' % (
            storage.__class__, obj.__class__))

    @reg.dispatch_method(reg.match_instance('obj'))
    def get_jslcrud_jsonprovider(self, obj):
        raise NotImplementedError('JSONProvider for %s' % obj.__class__)

    @reg.dispatch_method(reg.match_class('schema',
                                         lambda self, schema: schema))
    def get_jslcrud_jsontransform(self, schema):
        raise NotImplementedError('JSONTransform for %s' % schema)

    @reg.dispatch_method(reg.match_class('schema',
                                         lambda self, schema: schema))
    def get_jslcrud_formvalidators(self, schema):
        return []

    @reg.dispatch_method(reg.match_class('schema',
                                         lambda self, schema: schema))
    def get_jslcrud_identifierfields(self, schema):
        raise NotImplementedError('IdentifierFields for %s' % schema)

    @reg.dispatch_method(reg.match_class('schema',
                                         lambda self, schema: schema))
    def get_jslcrud_uuidfield(self, schema):
        return 'uuid'

    @reg.dispatch_method(
        reg.match_class('schema',
                        lambda self, schema, obj, request: schema))
    def get_jslcrud_default_identifier(self, schema, obj, request):
        return None

    @reg.dispatch_method(reg.match_instance('model', lambda self, obj: obj))
    def _jslcrud_rulesadapter(self, obj):
        raise NotImplementedError

    @reg.dispatch_method(reg.match_instance('model',
                                            lambda self, context: context))
    def _jslcrud_statemachine(self, context):
        raise NotImplementedError

    def get_jslcrud_compositekey_separator(self):
        morp_settings = getattr(self.settings, 'jslcrud', {})
        return morp_settings.get('compositekey_separator', '!!!')

    def jslcrud_join_identifier(self, *args):
        separator = self.get_jslcrud_compositekey_separator()
        return separator.join(args)
