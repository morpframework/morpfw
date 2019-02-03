import morepath
from jsonschema.validators import Draft4Validator
from jsonschema import validate, ValidationError
from .util import jsl_nullable
from .util import dataclass_to_jsl
from .const import SEPARATOR
from . import permission
from . import signals
from .log import logger
from rulez import validate_condition, parse_dsl, OperatorNotAllowedError
from morepath import reify
from DateTime import DateTime
from uuid import uuid4
from transitions import Machine
import copy
from .errors import StateUpdateProhibitedError, AlreadyExistsError, BlobStorageNotImplementedError
from .errors import UnprocessableError
from ..interfaces import IModel, ICollection
import json
import re


ALLOWED_SEARCH_OPERATORS = [
    'and', 'or', '==', 'in',
    '~', '!=', '>', '<', '>=',
    '<='
]

_marker = object()


class Collection(ICollection):

    create_view_enabled = True
    search_view_enabled = True
    search_allow_queryobject = True
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
            # FIXME: what is this for again? o_O
            self.data = request.app.get_dataprovider(self.schema, data,
                                                     self.storage)

    def search(self, query=None, offset=0, limit=None, order_by=None,
               secure=False):
        objs = self._search(query, offset, limit, order_by, secure)
        if secure and limit:
            nextpage = {'query': query,
                        'offset': offset + limit,
                        'limit': limit, 'order_by': order_by}
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

        prov = self.searchprovider()

        objs = prov.search(
            query, offset=offset, limit=limit, order_by=order_by)

        if secure:
            objs = list([obj for obj in objs if self.request.app.permits(
                self.request, obj, permission.View)])
        return list(objs)

    def aggregate(self, query=None, group=None, order_by=None):
        if query:
            validate_condition(query, ALLOWED_SEARCH_OPERATORS)
        prov = self.aggregateprovider()
        objs = prov.aggregate(query, group=group, order_by=order_by)
        return list(objs)

    def searchprovider(self):
        if self.app.get_searchprovider.by_args(self).all_matches:
            return self.app.get_searchprovider(self)
        return None

    def aggregateprovider(self):
        if self.app.get_aggregateprovider.by_args(self).all_matches:
            return self.app.get_aggregateprovider(self)
        return None

    def create(self, data):
        identifier = self.app.get_default_identifier(
            self.schema, data, self.request)
        if identifier and self.get(identifier):
            raise self.exist_exc(identifier)
        obj = self._create(data)
        obj.set_initial_state()
        dispatch = self.request.app.dispatcher(signals.OBJECT_CREATED)
        dispatch.dispatch(self.request, obj)
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
            'schema': dataclass_to_jsl(self.schema).get_schema(ordered=True),
            'links': self.links()
        }

    def links(self):
        request = self.request
        links = []
        if self.create_view_enabled:
            links.append({'rel': 'create',
                          'href': request.link(self),
                          'method': 'POST'})
        if self.search_view_enabled:
            links.append({'rel': 'search',
                          'href': request.link(self, '+search')})
        if self.aggregate_view_enabled:
            links.append({'rel': 'aggregate',
                          'href': request.link(self, '+aggregate')})
        links += self._links()
        return links

    def _links(self):
        return []


class Model(IModel):

    linkable = True
    update_view_enabled = True
    delete_view_enabled = True

    blobstorage_field: str = 'blobs'
    blob_fields: list = []
    protected_fields: list = [
        'id', 'blobs', 'state', 'xattrs',
        'modified', 'created', 'uuid',
        'creator', 'deleted'
    ]
    hidden_fields: list = []

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
        if self.statemachine():
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
        schema = dataclass_to_jsl(
            self.schema, nullable=True).get_schema(ordered=True)
        validate(data, schema)
        self.storage.update(self.identifier, data)
        dispatch = self.request.app.dispatcher(signals.OBJECT_UPDATED)
        dispatch.dispatch(self.request, self)

    def delete(self):
        dispatch = self.request.app.dispatcher(
            signals.OBJECT_TOBEDELETED)
        dispatch.dispatch(self.request, self)
        self.storage.delete(self.identifier, model=self)

    def save(self):
        if self.data.changed:
            data = self._raw_json()
            schema = dataclass_to_jsl(
                self.schema, nullable=True).get_schema(ordered=True)
            validate(data, schema)
            self.storage.update(self.identifier, data)

    def _raw_json(self):
        jsondata = self.app.get_jsonprovider(self.data)
        for k in self.hidden_fields:
            if k in jsondata:
                del jsondata[k]
        try:
            self.schema.validate(self.request, jsondata)
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
        return links

    def _links(self):
        return []

    def rulesprovider(self):
        return self.app.get_rulesprovider(self)

    def statemachine(self):
        if self.app.get_statemachine.by_args(self).all_matches:
            return self.app.get_statemachine(self)
        return None

    def xattrprovider(self):
        if self.app.get_xattrprovider.by_args(self).all_matches:
            return self.app.get_xattrprovider(self)
        return None

    def set_initial_state(self):
        self.statemachine()

    def _blob_guard(self, field):
        if self.blobstorage_field not in self.schema.__dataclass_fields__.keys():
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
