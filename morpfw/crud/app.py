import warnings
from urllib.parse import urlparse

import dectate
import morepath
import reg
from more.jsonschema import JsonSchemaApp
from more.signals import SignalApp
from sqlalchemy.orm import sessionmaker

from . import component as actions
from . import signals as signals
from .blobstorage.base import NullBlobStorage
from .model import Model

MARKER = object()


class App(JsonSchemaApp, signals.SignalApp):

    dataprovider = dectate.directive(actions.DataProviderAction)
    jsonprovider = dectate.directive(actions.JSONProviderAction)
    formvalidators = dectate.directive(actions.FormValidatorAction)
    identifierfield = dectate.directive(actions.IdentifierFieldAction)
    default_identifier = dectate.directive(actions.DefaultIdentifierAction)
    rulesprovider = dectate.directive(actions.RulesProviderAction)
    uuidfield = dectate.directive(actions.UUIDFieldAction)
    statemachine = dectate.directive(actions.StateMachineAction)
    searchprovider = dectate.directive(actions.SearchProviderAction)
    aggregateprovider = dectate.directive(actions.AggregateProviderAction)
    xattrprovider = dectate.directive(actions.XattrProviderAction)
    storage = dectate.directive(actions.StorageAction)
    storage_factory = dectate.directive(actions.StorageFactoryAction)
    blobstorage = dectate.directive(actions.BlobStorageAction)
    blobstorage_factory = dectate.directive(actions.BlobStorageFactoryAction)
    typeinfo = dectate.directive(actions.TypeInfoFactoryAction)
    metalink = dectate.directive(actions.MetalinkAction)
    authz_rule = dectate.directive(actions.AuthzRuleAction)

    def get_storage(self, model, request):
        blobstorage = self.get_blobstorage(model, request)
        return self._get_storage(model, request, blobstorage)

    def get_blobstorage(self, model, request):
        return self._get_blobstorage(model, request)

    def get_config_blobstorage(self, request: morepath.Request, name: str = None):
        config = self.settings.configuration.__dict__
        if name is None:
            uri = config["morpfw.blobstorage.uri"]
        else:
            uri = config["morpfw.blobstorage.uri.{}".format(name)]

        scheme = uri.split(":")[0]
        return self._get_blobstorage_factory(scheme)(request=request, uri=uri)

    def get_config_storage(self, request: morepath.Request, name: str = None):
        config = self.settings.configuration.__dict__
        if name is None:
            uri = config["morpfw.storage.uri"]
        else:
            uri = config["morpfw.storage.uri.{}".format(name)]

        parsed = urlparse(uri)
        return self._get_storage_factory(parsed.scheme)(request, uri)

    @reg.dispatch_method(
        reg.match_class("model"),
        reg.match_instance("request"),
        reg.match_instance("blobstorage"),
    )
    def _get_storage(self, model, request, blobstorage):
        raise NotImplementedError

    @reg.dispatch_method(reg.match_key("name"))
    def _get_storage_factory(self, name):
        raise NotImplementedError

    @reg.dispatch_method(reg.match_class("model"), reg.match_instance("request"))
    def _get_blobstorage(self, model, request):
        return NullBlobStorage()

    @reg.dispatch_method(reg.match_key("name"))
    def _get_blobstorage_factory(self, name):
        raise NotImplementedError

    @reg.dispatch(reg.match_key("name"))
    def get_authz_rule(self, name):
        raise NotImplementedError(name)

    @reg.dispatch_method(
        reg.match_class("schema", lambda self, schema, obj, storage: schema),
        reg.match_instance("obj"),
        reg.match_instance("storage"),
    )
    def get_dataprovider(self, schema, obj, storage):
        raise NotImplementedError(
            "Dataprovider for %s/%s" % (storage.__class__, obj.__class__)
        )

    @reg.dispatch_method(reg.match_instance("obj"))
    def get_jsonprovider(self, obj):
        raise NotImplementedError("JSONProvider for %s" % obj.__class__)

    @reg.dispatch_method(reg.match_class("schema", lambda self, schema: schema))
    def get_formvalidators(self, schema):
        return []

    @reg.dispatch_method(reg.match_class("schema", lambda self, schema: schema))
    def get_identifierfield(self, schema):
        raise NotImplementedError("IdentifierField for %s" % schema)

    @reg.dispatch_method(reg.match_class("schema", lambda self, schema: schema))
    def get_uuidfield(self, schema):
        return "uuid"

    @reg.dispatch_method(
        reg.match_class("schema", lambda self, schema, obj, request: schema)
    )
    def get_default_identifier(self, schema, obj, request):
        return None

    @reg.dispatch_method(reg.match_instance("model", lambda self, context: context))
    def get_rulesprovider(self, context):
        raise NotImplementedError

    @reg.dispatch_method(reg.match_instance("model", lambda self, context: context))
    def get_statemachine(self, context):
        raise NotImplementedError

    @reg.dispatch_method(reg.match_class("model"))
    def get_statemachine_factory(self, model):
        return None



    @reg.dispatch_method(reg.match_instance("model", lambda self, context: context))
    def get_searchprovider(self, context):
        raise NotImplementedError

    @reg.dispatch_method(reg.match_instance("model", lambda self, context: context))
    def get_aggregateprovider(self, context):
        raise NotImplementedError

    @reg.dispatch_method(reg.match_instance("model", lambda self, context: context))
    def get_xattrprovider(self, context):
        raise NotImplementedError

    @reg.dispatch_method(reg.match_key("name"))
    def _get_metalinkprovider_by_name(self, name, request):
        raise NotImplementedError

    @reg.dispatch_method(reg.match_instance("model"))
    def _get_metalinkprovider_by_model(self, model, request):
        raise NotImplementedError

    def get_metalink(self, obj: object, request, **kwargs):
        metalink = self._get_metalinkprovider_by_model(obj, request)
        return metalink.link(obj, **kwargs)

    def resolve_metalink(self, link: dict, request):
        metalink = self._get_metalinkprovider_by_name(link["type"], request)
        return metalink.resolve(link)

    @reg.dispatch_method(reg.match_key("name"))
    def get_typeinfo_factory(self, name):
        raise NotImplementedError

    def get_typeinfo(self, name, request):
        typeinfo = self.config.type_registry.get_typeinfo(name=name, request=request)
        return typeinfo

    def get_typeinfo_by_schema(self, schema, request):
        typeinfo = self.config.type_registry.get_typeinfo_by_schema(
            schema=schema, request=request
        )
        return typeinfo

    def get_compositekey_separator(self):
        raise Exception("BOOO")

    def join_identifier(self, *args):
        raise Exception("BOOO")

    def permits(self, request: morepath.Request, context: Model, permission: str):
        identity = request.identity
        return self._permits(identity, context, permission)

    def get_config(self, key, default=MARKER):
        registry = self.settings.configuration.__dict__
        if default is MARKER:
            return registry.get(key)
        return registry.get(key, default)

    def get_template(self, template):
        def render(content, request):
            return content

        return self.config.template_engine_registry.get_template_render(
            template, render
        )
