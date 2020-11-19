import copy
import json
from logging import warn
import re
from uuid import uuid4
import dataclasses
import morepath
import rulez
from DateTime import DateTime
from jsonschema import ValidationError as JSLValidationError
from jsonschema import validate
from jsonschema.validators import Draft4Validator
from morepath import reify
from rulez import OperatorNotAllowedError
from rulez import field as rfield
from rulez import parse_dsl, validate_condition
from transitions import Machine
import logging
from ..interfaces import ICollection, IModel, IStorage
from ..memoizer import requestmemoize
from . import permission, signals
from .const import SEPARATOR
from .errors import (
    AlreadyExistsError,
    BlobStorageNotImplementedError,
    FormValidationError,
    StateUpdateProhibitedError,
    UnprocessableError,
    ValidationError,
)
from .log import logger
from inverter import dc2colanderjson
from inverter import dc2jsl
import warnings
from ..request import Request

ALLOWED_SEARCH_OPERATORS = [
    "and",
    "or",
    "==",
    "in",
    "~",
    "!=",
    ">",
    "<",
    ">=",
    "<=",
    "match",
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
        if key not in self.schema.__dataclass_fields__:
            raise KeyError(key)
        self.data[key] = value

    def __getitem__(self, key):
        if key not in self.schema.__dataclass_fields__:
            raise KeyError(key)
        return self.data[key]

    def __delitem__(self, key):
        if key not in self.schema.__dataclass_fields__:
            raise KeyError(key)
        del self.data[key]

    def __init__(self, request: Request, storage: IStorage, data=None):
        self.request = request
        self.app = request.app
        self.storage = storage
        self.data = None
        if data:
            # FIXME: what is this for again? o_O
            self.data = request.app.get_dataprovider(self.schema, data, self.storage)

    def search(self, query=None, offset=0, limit=None, order_by=None, secure=False):
        objs = self._search(query, offset, limit, order_by, secure)
        if secure and limit:
            nextpage = {
                "query": query,
                "offset": offset + limit,
                "limit": limit,
                "order_by": order_by,
            }
            while len(objs) < limit:
                nextobjs = self._search(secure=True, **nextpage)
                if len(nextobjs) == 0:
                    return list(objs[:limit])
                nextpage["offset"] = nextpage["offset"] + limit
                objs = objs + nextobjs
        return objs

    @requestmemoize()
    def all(self):
        return self.search()

    @requestmemoize()
    def count(self):
        return self.aggregate(group={"count": {"function": "count", "field": "uuid"}})[
            0
        ]["count"]

    @requestmemoize()
    def max_id(self):
        return self.aggregate(group={"max_id": {"function": "max", "field": "id"}})[0][
            "max_id"
        ]

    @requestmemoize()
    def min_id(self):
        return self.aggregate(group={"min_id": {"function": "min", "field": "id"}})[0][
            "min_id"
        ]

    def _search(self, query=None, offset=0, limit=None, order_by=None, secure=False):
        if query:
            validate_condition(query, ALLOWED_SEARCH_OPERATORS)

        if order_by is None:
            order_by = ("created", "desc")

        objs = self.storage.search(
            self, query, offset=offset, limit=limit, order_by=order_by
        )

        if secure:
            objs = list(
                [
                    obj
                    for obj in objs
                    if self.request.app.permits(self.request, obj, permission.View)
                ]
            )
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

    def create(self, data, deserialize=True):
        data = self.schema.validate(
            self.request, data, deserialize=deserialize, context=self
        )
        self.before_create(data)
        identifier = self.app.get_default_identifier(self.schema, data, self.request)
        if identifier and self.get(identifier):
            raise self.exist_exc(identifier)
        data = self.storage.set_schema_defaults(data)
        for fname, field in self.schema.__dataclass_fields__.items():
            if data[fname] is not None:
                continue
            dc_default_factory = field.default_factory
            if not isinstance(dc_default_factory, dataclasses._MISSING_TYPE):
                data[fname] = dc_default_factory()

            if data[fname] is not None:
                continue

            default_factory = field.metadata.get("default_factory", None)
            if default_factory:
                data[fname] = default_factory(self, self.request)
        unique_constraint = getattr(self.schema, "__unique_constraint__", None)
        if unique_constraint:
            unique_search = []
            msg = []
            for c in unique_constraint:
                unique_search.append(rulez.field[c] == data[c])
                msg.append(f"{c}=({data[c]})")
            if self.search(rulez.and_(*unique_search)):
                raise self.exist_exc(" ".join(msg))

        obj = self._create(data)
        obj.set_initial_state()
        dispatch = self.request.app.dispatcher(signals.OBJECT_CREATED)
        dispatch.dispatch(self.request, obj)
        obj.after_created()
        obj.save()
        return obj

    def _create(self, data):
        return self.storage.create(self, data)

    @requestmemoize()
    def get(self, identifier):
        if isinstance(identifier, list) or isinstance(identifier, tuple):
            identifier = self.request.app.join_identifier(*identifier)
        return self.storage.get(self, identifier)

    @requestmemoize()
    def get_by_uuid(self, uuid):
        return self.storage.get_by_uuid(self, uuid)

    def json(self):
        return {
            "schema": dc2jsl.convert(self.schema).get_schema(ordered=True),
            "links": self.links(),
        }

    def links(self):
        request = self.request
        links = []
        if self.create_view_enabled:
            links.append(
                {"rel": "create", "href": request.link(self), "method": "POST"}
            )
        if self.search_view_enabled:
            links.append({"rel": "search", "href": request.link(self, "+search")})
        if self.aggregate_view_enabled:
            links.append({"rel": "aggregate", "href": request.link(self, "+aggregate")})
        links += self._links()
        return links

    def _links(self):
        return []


class Model(IModel):

    linkable = True
    update_view_enabled = True
    delete_view_enabled = True

    blobstorage_field: str = "blobs"
    blob_fields: list = []
    blob_field_options: dict = {}
    protected_fields: list = [
        "id",
        "blobs",
        "state",
        "xattrs",
        "modified",
        "created",
        "uuid",
        "creator",
        "deleted",
    ]
    hidden_fields: list = []

    def __setitem__(self, key, value):
        warnings.warn(
            "Value assignment through model will be removed", DeprecationWarning
        )
        self.data[key] = value

    def __getitem__(self, key):
        return self.data[key]

    def __delitem__(self, key):
        warnings.warn(
            "Value deletion through model will be removed", DeprecationWarning
        )
        del self.data[key]

    def __dict__(self):
        return self.data.as_dict()

    def title(self):
        return self["uuid"]

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
        idfield = self.app.get_identifierfield(self.schema)
        identifier = self.data.get(idfield)
        if identifier is None:
            identifier = self.app.get_default_identifier(
                self.schema, self.data, self.request
            )
            if identifier is None:
                return None
            return identifier
        self._cached_identifier = identifier
        return identifier

    @property
    def uuid(self):
        uuid_field = self.app.get_uuidfield(self.schema)
        return self.data[uuid_field]

    def __init__(self, request, collection, data):
        self.collection = collection
        self.request = request
        self.storage = collection.storage
        self.app = request.app
        self.data = request.app.get_dataprovider(self.schema, data, self.storage)
        self._cached_identifier = None
        super().__init__(request, collection, data)

    def update(self, newdata: dict, secure: bool = False, deserialize: bool = True):
        if secure:
            if "state" in newdata:
                raise StateUpdateProhibitedError()
            for protected in self.protected_fields:
                if protected in newdata.keys():
                    raise UnprocessableError(
                        "%s is not allowed to be updated in this context" % protected
                    )

        if deserialize:
            data = self.data.as_json()
        else:
            data = self.data.as_dict()
        self.before_update(newdata)
        data.update(newdata)
        self.schema.validate(
            self.request, data, deserialize=deserialize, update_mode=True, context=self
        )
        unique_constraint = getattr(self.schema, "__unique_constraint__", None)
        if unique_constraint:
            unique_search = []
            msg = []
            for c in unique_constraint:
                unique_search.append(rulez.field[c] == data[c])
                msg.append(f"{c}=({data[c]})")
            res = self.collection.search(rulez.and_(*unique_search))
            if res:
                if res[0].identifier != self.identifier:
                    raise self.collection.exist_exc(" ".join(msg))

        if deserialize:
            cschema = dc2colanderjson.convert(self.schema, request=self.request)
            cs = cschema()
            cs = cs.bind(context=self, request=self.request)
            data = cs.deserialize(data)
        self.storage.update(self.collection, self.identifier, data)
        dispatch = self.request.app.dispatcher(signals.OBJECT_UPDATED)
        dispatch.dispatch(self.request, self)
        self.after_updated()

    def delete(self, **kwargs):
        dispatch = self.request.app.dispatcher(signals.OBJECT_TOBEDELETED)
        dispatch.dispatch(self.request, self)
        if not self.before_delete():
            return
        blob_uuids = []
        for blobfield in self.blob_fields:
            if self.blobstorage_field not in self.data.keys():
                uuid = None
            elif not self.data[self.blobstorage_field]:
                uuid = None
            elif not blobfield in self.data[self.blobstorage_field]:
                uuid = None
            else:
                uuid = self.data[self.blobstorage_field][blobfield]
            if uuid:
                blob_uuids.append(uuid)
        self.storage.delete(self.identifier, model=self, **kwargs)
        for blob_uuid in blob_uuids:
            self.storage.delete_blob(blob_uuid)

    def save(self):
        if self.data.changed:
            data = self.as_dict()
            data = self.schema.validate(
                self.request, data, deserialize=False, context=self
            )
            self.storage.update(self.collection, self.identifier, data)

    def _base_json(self, exclude_metadata=False):

        exclude_fields = self.hidden_fields
        if exclude_metadata:
            from .schema import Schema

            exclude_fields += list(Schema.__dataclass_fields__.keys())
        cschema = dc2colanderjson.convert(
            self.schema, exclude_fields=exclude_fields, request=self.request
        )
        cs = cschema()
        cs = cs.bind(context=self, request=self.request)
        return cs.serialize(self.data.as_dict())

    @requestmemoize()
    def base_json(self):
        return self._base_json()

    @requestmemoize()
    def data_json(self):
        return self._base_json(exclude_metadata=True)

    def _json(self):
        return self.base_json()

    def json(self):
        if self.linkable:
            return {"data": self._json(), "links": self.links()}
        return self._json()

    def as_json(self):
        return self.data.as_json()

    def as_dict(self):
        return self.data.as_dict()

    @requestmemoize()
    def links(self):
        links = []
        links.append({"rel": "self", "href": self.request.link(self)})
        if self.update_view_enabled:
            links.append(
                {"rel": "update", "href": self.request.link(self), "method": "PATCH"}
            )
        if self.delete_view_enabled:
            links.append(
                {"rel": "delete", "href": self.request.link(self), "method": "DELETE"}
            )
        if self.statemachine_view_enabled:
            links.append(
                {
                    "rel": "statemachine",
                    "href": self.request.link(self, "+statemachine"),
                    "method": "POST",
                }
            )
        links += self._links()
        return links

    def _links(self):
        return []

    @requestmemoize()
    def rulesprovider(self):
        return self.app.get_rulesprovider(self)

    @requestmemoize()
    def statemachine(self):
        if self.app.get_statemachine.by_args(self).all_matches:
            return self.app.get_statemachine(self)
        return None

    @requestmemoize()
    def xattrprovider(self):
        if self.app.get_xattrprovider.by_args(self).all_matches:
            return self.app.get_xattrprovider(self)
        return None

    def set_initial_state(self):
        self.statemachine()

    def _blob_guard(self, field):
        if self.blobstorage_field not in self.schema.__dataclass_fields__.keys():
            raise BlobStorageNotImplementedError(
                "Object does not implement blobs store"
            )
        if field not in self.blob_fields:
            raise BlobStorageNotImplementedError(
                "Field %s not allowed for blobstorage" % field
            )

    def put_blob(
        self, field, fileobj, filename, mimetype=None, size=None, encoding=None
    ):
        self._blob_guard(field)
        allowed_types = self.blob_field_options.get(field, {}).get("allowed_types", [])
        if mimetype and allowed_types and mimetype not in allowed_types:
            raise ValueError("Mimetype %s not allowed" % mimetype)
        self.before_blobput(field, fileobj, filename, mimetype, size, encoding)
        blob_data = self.data[self.blobstorage_field] or {}
        existing = blob_data.get(field, None)
        blob = self.storage.put_blob(fileobj, filename, mimetype, size, encoding)
        blob_data[field] = blob.uuid
        self.update({self.blobstorage_field: blob_data})
        if existing:
            self.storage.delete_blob(existing)
        self.after_blobput(field, blob)
        self.save()
        return blob

    def get_blob(self, field):
        if self.blobstorage_field not in self.data.keys():
            return None
        if not self.data[self.blobstorage_field]:
            return None
        if not field in self.data[self.blobstorage_field]:
            return None
        uuid = self.data[self.blobstorage_field][field]
        blob = self.storage.get_blob(uuid)
        return blob

    def delete_blob(self, field):
        if self.blobstorage_field not in self.data.keys():
            return None
        if not self.data[self.blobstorage_field]:
            return None
        if not field in self.data[self.blobstorage_field]:
            return None
        uuid = self.data[self.blobstorage_field][field]
        if not self.before_blobdelete(field):
            return
        self.storage.delete_blob(uuid)
        self.save()
