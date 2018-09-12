from .app import App
import jsl
from jsonschema.validators import Draft4Validator
from jsonschema import validate, ValidationError
from .util import jsl_nullable
from .const import SEPARATOR
from . import permission
from . import signals
from .log import logger
from rulez import validate_condition
from morepath import reify
from DateTime import DateTime
import jsl
from uuid import uuid4
from transitions import Machine
import copy
from .errors import StateUpdateProhibitedError, AlreadyExistsError


ALLOWED_SEARCH_OPERATORS = [
    'and', 'or', '==', 'in',
    '~', '!=', '>', '<', '>=',
    '<='
]


@App.jslcrud_jsontransfrom(schema=jsl.Document)
def default_jsontransform(request, context, data):
    return data


class Schema(jsl.Document):

    uuid = jsl.StringField(required=False)
    creator = jsl.StringField(required=False)
    created = jsl.DateTimeField(required=False)
    modified = jsl.DateTimeField(required=False)


@App.jslcrud_identifierfields(schema=Schema)
def default_identifierfields(schema):
    return ['uuid']


@App.jslcrud_default_identifier(schema=Schema)
def default_identifier(schema, obj, request):
    if obj.get('uuid', None) is None:
        return uuid4().hex


def permits(request, obj, permission, app=None):
    if app is None:
        app = request.app
    return app._permits(request.identity, obj, permission)


class Collection(object):

    create_view_enabled = True
    search_view_enabled = True
    aggregate_view_enabled = True

    @property
    def schema(self):
        raise NotImplementedError

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, key):
        return self.data[key]

    def __delitem__(self, key):
        del self.data[key]

    def __init__(self, request, storage, data=None):
        self.request = request
        self.app = request.app
        self.storage = storage
        self.data = None
        if data:
            self.data = request.app.get_jslcrud_dataprovider(self.schema, data,
                                                             self.storage)

    def search(self, query=None, offset=0, limit=None, order_by=None,
               secure=False):
        objs = self._search(query, offset, limit, order_by, secure)
        if secure and limit:
            nextpage = {'query': query, 'offset': offset +
                        limit, 'limit': limit, 'order_by': order_by}
            while len(objs) < limit:
                nextobjs = self._search(secure=True, **nextpage)
                if len(nextobjs) == 0:
                    return list(objs[:limit])
                nextpage['offset'] = nextpage['offset'] + limit
                objs = objs + nextobjs
        return objs

    def _search(self, query=None, offset=0, limit=None, order_by=None,
                secure=False):
        if query:
            validate_condition(query, ALLOWED_SEARCH_OPERATORS)
        objs = self.storage.search(
            query, offset=offset, limit=limit, order_by=order_by)

        if secure:
            objs = list([obj for obj in objs if permits(
                self.request, obj, permission.View)])
        return list(objs)

    def aggregate(self, query=None, group=None, order_by=None):
        if query:
            validate_condition(query, ALLOWED_SEARCH_OPERATORS)
        objs = self.storage.aggregate(query, group=group, order_by=order_by)
        return list(objs)

    def create(self, data):
        identifier = self.app.get_jslcrud_default_identifier(
            self.schema, data, self.request)
        if identifier and self.get(identifier):
            raise AlreadyExistsError(identifier)
        obj = self._create(data)
        obj.set_initial_state()
        self.request.app.jslcrud_publish(self.request,
                                         obj, signals.OBJECT_CREATED)
        return obj

    def _create(self, data):
        data = self.storage.set_schema_defaults(data)
        return self.storage.create(data)

    def get(self, identifier):
        if isinstance(identifier, list) or isinstance(identifier, tuple):
            identifier = self.request.app.jslcrud_join_identifier(*identifier)
        return self.storage.get(identifier)

    def get_by_uuid(self, uuid):
        return self.storage.get_by_uuid(uuid)

    def json(self):
        return {
            'schema': self.schema.get_schema(ordered=True),
            'links': self.links()
        }

    def links(self):
        request = self.request
        links = [{'rel': 'create',
                  'href': request.link(self, '+create'),
                  'method': 'POST'},
                 {'rel': 'search',
                  'href': request.link(self, '+search')}]
        links += self._links()
        return links

    def _links(self):
        return []


class Model(object):

    linkable = True
    update_view_enabled = True
    delete_view_enabled = True

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, key):
        return self.data[key]

    def __delitem__(self, key):
        del self.data[key]

    @property
    def statemachine_view_enabled(self):
        if self.state_machine():
            return True
        return False

    @property
    def schema(self):
        raise NotImplementedError

    @property
    def identifier(self):
        if self._cached_identifier:
            return self._cached_identifier
        res = []
        for f in self.app.get_jslcrud_identifierfields(self.schema):
            d = self.data.get(f)
            if d is not None:
                d = str(d)
            res.append(d)
        if None in res:
            identifier = self.app.get_jslcrud_default_identifier(
                self.schema, self.data, self.request)
            if identifier is None:
                return None
            if isinstance(identifier, list) or isinstance(identifier, tuple):
                identifier = self.app.jslcrud_join_identifier(*identifier)
            self.storage.set_identifier(self.data, identifier)
            self._cached_identifier = identifier
            return identifier
        separator = self.request.app.get_jslcrud_compositekey_separator()
        identifier = separator.join(res)
        self._cached_identifier = identifier
        return identifier

    @property
    def uuid(self):
        uuid_field = self.app.get_jslcrud_uuidfield(self.schema)
        return self.data[uuid_field]

    def __init__(self, request, storage, data):
        self.request = request
        self.storage = storage
        self.app = request.app
        self.data = request.app.get_jslcrud_dataprovider(self.schema, data,
                                                         self.storage)
        self._cached_identifier = None

    def update(self, newdata):
        if 'state' in newdata:
            raise StateUpdateProhibitedError()

        data = self._raw_json()
        data.update(newdata)
        schema = jsl_nullable(self.schema).get_schema(ordered=True)
        validate(data, schema)
        self.storage.update(self.identifier, data)
        self.request.app.jslcrud_publish(
            self.request, self, signals.OBJECT_UPDATED)

    def delete(self):
        self.request.app.jslcrud_publish(
            self.request, self, signals.OBJECT_TOBEDELETED)
        self.storage.delete(self.identifier, model=self)

    def save(self):
        if self.data.changed:
            data = self._raw_json()
            schema = jsl_nullable(self.schema).get_schema(ordered=True)
            validate(data, schema)
            self.storage.update(self.identifier, data)

    def _raw_json(self):
        schema = jsl_nullable(self.schema).get_schema(ordered=True)
        jsondata = self.app.get_jslcrud_jsonprovider(self.data)
        jsondata = self.app.get_jslcrud_jsontransform(
            self.schema)(self.request, self, copy.deepcopy(jsondata))
        jsondata = self.rules_adapter().transform_json(copy.deepcopy(jsondata))
        try:
            validate(jsondata, schema)
        except ValidationError as e:
            logger.warn('%s(%s) : %s' % (self.schema.__name__,
                                         '/'.join(list(e.path)), e.message))
        return jsondata

    def _json(self):
        return self._raw_json()

    def json(self):
        if self.linkable:
            return {
                'data': self._json(),
                'links': self.links()
            }
        return self._json()

    def links(self):
        links = []
        links.append({
            'rel': 'self',
            'href': self.request.link(self)
        })
        if self.update_view_enabled:
            links.append({
                'rel': 'update',
                'href': self.request.link(self),
                'method': 'PATCH'
            })
        if self.delete_view_enabled:
            links.append({
                'rel': 'delete',
                'href': self.request.link(self),
                'method': 'DELETE'
            })
        if self.statemachine_view_enabled:
            links.append({
                'rel': 'statemachine',
                'href': self.request.link(self, '+statemachine'),
                'method': 'POST'
            })
        links += self._links()
        links += self.rules_adapter().links()
        return links

    def _links(self):
        return []

    def rules_adapter(self):
        return self.app._jslcrud_rulesadapter(self)

    def state_machine(self):
        if self.app._jslcrud_statemachine.by_args(self).all_matches:
            return self.app._jslcrud_statemachine(self)
        return None

    def set_initial_state(self):
        self.state_machine()


class Adapter(object):

    def __init__(self, model: Model):
        self.model = model
        self.request = model.request
        self.app = model.app

    @property
    def schema(self):
        return self.model.schema

    @property
    def identifier(self):
        return self.model.identifier

    @property
    def data(self):
        return self.model.data

    def json(self):
        return self.model.json()

    def update(self, *args, **kwargs):
        return self.model.update(*args, **kwargs)

    def delete(self):
        return self.model.delete()

    def transform_json(self, data):
        return data

    def links(self):
        return []

    def __repr__(self):
        return "<Adapted %s:(%s)>" % (self.__class__.__name__, self.model)


class StateMachine(object):

    @property
    def states(self):
        raise NotImplementedError

    @property
    def transitions(self):
        raise NotImplementedError

    def __init__(self, context):
        self._context = context
        self._request = context.request
        self._app = context.request.app
        initial = self.state or self.states[0]
        self._machine = Machine(
            model=self, transitions=self.transitions,
            states=self.states, initial=initial)

    @property
    def state(self):
        try:
            return self._context.data['state']
        except KeyError:
            return None

    @state.setter
    def state(self, val):
        self._context.data['state'] = val


@App.jslcrud_rulesadapter(model=Model)
def get_default_rulesadapter(obj):
    return Adapter(obj)
