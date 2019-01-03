from jsonschema.validators import Draft4Validator
from jsonschema import validate, ValidationError
from .util import jsl_nullable
from .util import jsonobject_to_jsl
from .const import SEPARATOR
from . import permission
from . import signals
from .log import logger
from rulez import validate_condition
from morepath import reify
from DateTime import DateTime
from uuid import uuid4
from transitions import Machine
import copy
from .errors import StateUpdateProhibitedError, AlreadyExistsError, BlobStorageNotImplementedError
from .errors import UnprocessableError
import jsonobject
from ..interfaces import IModel


ALLOWED_SEARCH_OPERATORS = [
    'and', 'or', '==', 'in',
    '~', '!=', '>', '<', '>=',
    '<='
]

_marker = object()


class Collection(object):

    create_view_enabled = True
    search_view_enabled = True
    aggregate_view_enabled = True

    exist_exc = AlreadyExistsError

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
            self.data = request.app.get_dataprovider(self.schema, data,
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
            objs = list([obj for obj in objs if self.request.app.permits(
                self.request, obj, permission.View)])
        return list(objs)

    def aggregate(self, query=None, group=None, order_by=None):
        if query:
            validate_condition(query, ALLOWED_SEARCH_OPERATORS)
        objs = self.storage.aggregate(query, group=group, order_by=order_by)
        return list(objs)

    def create(self, data):
        identifier = self.app.get_default_identifier(
            self.schema, data, self.request)
        if identifier and self.get(identifier):
            raise self.exist_exc(identifier)
        obj = self._create(data)
        obj.set_initial_state()
        self.request.app.signal_publish(self.request,
                                        obj, signals.OBJECT_CREATED)
        return obj

    def _create(self, data):
        data = self.storage.set_schema_defaults(data)
        return self.storage.create(data)

    def get(self, identifier):
        if isinstance(identifier, list) or isinstance(identifier, tuple):
            identifier = self.request.app.join_identifier(*identifier)
        return self.storage.get(identifier)

    def get_by_uuid(self, uuid):
        return self.storage.get_by_uuid(uuid)

    def json(self):
        return {
            'schema': jsonobject_to_jsl(self.schema).get_schema(ordered=True),
            'links': self.links()
        }

    def links(self):
        request = self.request
        links = [{'rel': 'create',
                  'href': request.link(self),
                  'method': 'POST'},
                 {'rel': 'search',
                  'href': request.link(self, '+search')}]
        links += self._links()
        return links

    def _links(self):
        return []


class Model(IModel):

    linkable = True
    update_view_enabled = True
    delete_view_enabled = True

    blobstorage_field = 'blobs'
    blob_fields = []
    protected_fields = [
        'id',  'blobs', 'state',  'xattrs',
        'modified', 'created', 'uuid',
        'creator', 'deleted'
    ]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, key):
        return self.data[key]

    def __delitem__(self, key):
        del self.data[key]

    def __dict__(self):
        return self.data.as_dict()

    @property
    def statemachine_view_enabled(self):
        if self.state_machine():
            return True
        return False

    @property
    def xattr_view_enabled(self):
        if self.xattrprovider():
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
        for f in self.app.get_identifierfields(self.schema):
            d = self.data.get(f)
            if d is not None:
                d = str(d)
            res.append(d)
        if None in res:
            identifier = self.app.get_default_identifier(
                self.schema, self.data, self.request)
            if identifier is None:
                return None
            if isinstance(identifier, list) or isinstance(identifier, tuple):
                identifier = self.app.join_identifier(*identifier)
            self.storage.set_identifier(self.data, identifier)
            self._cached_identifier = identifier
            return identifier
        separator = self.request.app.get_compositekey_separator()
        identifier = separator.join(res)
        self._cached_identifier = identifier
        return identifier

    @property
    def uuid(self):
        uuid_field = self.app.get_uuidfield(self.schema)
        return self.data[uuid_field]

    def __init__(self, request, storage, data):
        self.request = request
        self.storage = storage
        self.app = request.app
        self.data = request.app.get_dataprovider(self.schema, data,
                                                 self.storage)
        self._cached_identifier = None
        super().__init__(request, storage, data)

    def update(self, newdata, secure=False):

        if secure:
            if 'state' in newdata:
                raise StateUpdateProhibitedError()
            for protected in self.protected_fields:
                if protected in newdata.keys():
                    raise UnprocessableError(
                        "%s is not allowed to be updated in this context" % protected)

        data = self._raw_json()
        data.update(newdata)
        schema = jsonobject_to_jsl(
            self.schema, nullable=True).get_schema(ordered=True)
        validate(data, schema)
        self.storage.update(self.identifier, data)
        self.request.app.signal_publish(
            self.request, self, signals.OBJECT_UPDATED)

    def delete(self):
        self.request.app.signal_publish(
            self.request, self, signals.OBJECT_TOBEDELETED)
        self.storage.delete(self.identifier, model=self)

    def save(self):
        if self.data.changed:
            data = self._raw_json()
            schema = jsonobject_to_jsl(
                self.schema, nullable=True).get_schema(ordered=True)
            validate(data, schema)
            self.storage.update(self.identifier, data)

    def _raw_json(self):
        schema = jsonobject_to_jsl(
            self.schema, nullable=True).get_schema(ordered=True)
        jsondata = self.app.get_jsonprovider(self.data)
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

    def as_json(self):
        return self.data.as_json()

    def as_dict(self):
        return self.data.as_dict()

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
        return self.app.get_rulesadapter(self)

    def state_machine(self):
        return self.statemachine()

    def statemachine(self):
        if self.app.get_statemachine.by_args(self).all_matches:
            return self.app.get_statemachine(self)
        return None

    def xattrprovider(self):
        if self.app.get_xattrprovider.by_args(self).all_matches:
            return self.app.get_xattrprovider(self)
        return None

    def set_initial_state(self):
        self.state_machine()

    def _blob_guard(self, field):
        if self.blobstorage_field not in self.schema._properties_by_attr.keys():
            raise BlobStorageNotImplementedError(
                'Object does not implement blobs store')
        if field not in self.blob_fields:
            raise BlobStorageNotImplementedError(
                'Field %s not allowed for blobstorage' % field)

    def put_blob(self, field, fileobj, filename, mimetype=None, size=None, encoding=None):
        self._blob_guard(field)
        blob_data = self.data[self.blobstorage_field] or {}
        existing = blob_data.get(field, None)
        blob = self.storage.put_blob(
            fileobj, filename, mimetype, size, encoding)
        blob_data[field] = blob.uuid
        self.update({self.blobstorage_field: blob_data})
        if existing:
            self.storage.delete_blob(existing)
        return blob

    def get_blob(self, field):
        if not self.data[self.blobstorage_field]:
            return None
        uuid = self.data[self.blobstorage_field][field]
        blob = self.storage.get_blob(uuid)
        return blob

    def delete_blob(self, field):
        uuid = self.data[self.blobstorage_field][field]
        self.storage.delete_blob(uuid)


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

    def get_triggers(self):
        return [i for i in self._machine.get_triggers(self.state) if not i.startswith('to_')]


class XattrProvider(object):

    @property
    def schema(self):
        raise NotImplementedError

    def __init__(self, context):
        self.context = context
        self.request = context.request
        self.app = context.request.app

    def jsonschema(self):
        schema = jsonobject_to_jsl(
            self.schema, nullable=True).get_schema(ordered=True)
        return {
            'schema': schema
        }

    def as_json(self):
        raise NotImplementedError

    def as_dict(self):
        raise NotImplementedError

    def process_update(self, newdata: dict):
        data = self.as_json()
        data.update(newdata)
        schema = jsonobject_to_jsl(
            self.schema, nullable=True).get_schema(ordered=True)
        validate(data, schema)
        self.update(data)

    def update(self, newdata: dict):
        raise NotImplementedError

    def __setitem__(self, key, value):
        raise NotImplementedError

    def __getitem__(self, key):
        raise NotImplementedError

    def __delitem__(self, key):
        raise NotImplementedError

    def get(self, key, default=_marker):
        raise NotImplementedError
