from more.jsonschema import JsonSchemaApp
from . import signals as signals
from sqlalchemy.orm import sessionmaker
import dectate
import reg
from more.signals import SignalApp
from . import component as actions

Session = sessionmaker()


class App(JsonSchemaApp, signals.SignalApp):
    jslcrud_dataprovider = dectate.directive(actions.DataProviderAction)
    jslcrud_jsonprovider = dectate.directive(actions.JSONProviderAction)
    jslcrud_jsontransfrom = dectate.directive(actions.JSONTransformAction)
    jslcrud_formvalidators = dectate.directive(actions.FormValidatorAction)
    jslcrud_identifierfields = dectate.directive(
        actions.IdentifierFieldsAction)
    jslcrud_default_identifier = dectate.directive(
        actions.DefaultIdentifierAction)

    jslcrud_rulesadapter = dectate.directive(actions.RulesAdapterAction)
    jslcrud_uuidfield = dectate.directive(actions.UUIDFieldAction)
    jslcrud_statemachine = dectate.directive(actions.StateMachineAction)

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
