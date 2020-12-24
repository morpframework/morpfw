import os
import pprint
import typing
from dataclasses import dataclass, field

import morpfw.crud.signals as signals
from elasticsearch import Elasticsearch
from more.basicauth import BasicAuthIdentityPolicy
from more.transaction import TransactionApp
from morepath.reify import reify
from morepath.request import Request
from morpfw.crud.blobstorage.fsblobstorage import FSBlobStorage
from morpfw.crud.model import Collection, Model
from morpfw.crud.schema import Schema
from morpfw.crud.storage.elasticsearchstorage import ElasticSearchStorage
from morpfw.request import ESCapableRequest
from sqlalchemy.orm import sessionmaker
from zope.sqlalchemy import register as register_session

from ..common import get_client
from .crud_common import FSBLOB_DIR
from .crud_common import App as BaseApp
from .crud_common import (
    BlobObjectCollection,
    BlobObjectModel,
    NamedObjectCollection,
    NamedObjectModel,
)
from .crud_common import ObjectSchema as BaseObjectSchema
from .crud_common import (
    ObjectXattrProvider,
    ObjectXattrSchema,
    PageCollection,
    PageModel,
    PageSchema,
    run_jslcrud_test,
)

Session = sessionmaker()
register_session(Session)


class App(BaseApp, TransactionApp):

    request_class = ESCapableRequest


class PageStorage(ElasticSearchStorage):
    index_name = "test-page"
    refresh = True
    model = PageModel


@App.path(model=PageCollection, path="pages")
def collection_factory(request):
    storage = PageStorage(request)
    return PageCollection(request, storage)


@App.path(model=PageModel, path="pages/{identifier}")
def model_factory(request, identifier):
    col = collection_factory(request)
    return col.get(identifier)


@App.typeinfo(name="tests.page", schema=PageSchema)
def get_page_typeinfo(request):
    return {
        "title": "Page",
        "description": "Page type",
        "schema": PageSchema,
        "collection": PageCollection,
        "collection_factory": collection_factory,
        "model": PageModel,
        "model_factory": model_factory,
    }


@dataclass
class ObjectSchema(BaseObjectSchema):

    id: typing.Optional[str] = None


@App.identifierfield(schema=ObjectSchema)
def object_identifierfield(schema):
    return "id"


@App.default_identifier(schema=ObjectSchema)
def object_default_identifier(schema, obj, request):
    return None


class ObjectModel(Model):
    schema = ObjectSchema


@App.xattrprovider(model=ObjectModel)
def get_xattr_provider(context):
    return ObjectXattrProvider(context)


class ObjectCollection(Collection):
    schema = ObjectSchema


@App.subscribe(signal=signals.OBJECT_CREATED, model=ObjectModel)
def object_created(app, request, obj, signal):
    obj.data["created_flag"] = True


@App.subscribe(signal=signals.OBJECT_UPDATED, model=ObjectModel)
def object_updated(app, request, obj, signal):
    obj.data["updated_flag"] = True


class ObjectStorage(ElasticSearchStorage):
    index_name = "test-object"
    refresh = True
    auto_id = True
    model = ObjectModel


@App.json(model=ObjectCollection, name="get_uuid")
def get_object_by_uuid(context, request):
    uuid = request.GET.get("uuid")
    return context.get_by_uuid(uuid).json()


@App.path(model=ObjectCollection, path="objects")
def object_collection_factory(request):
    storage = ObjectStorage(request)
    return ObjectCollection(request, storage)


@App.path(model=ObjectModel, path="objects/{identifier}")
def object_model_factory(request, identifier):
    col = object_collection_factory(request)
    return col.get(identifier)


class NamedObjectStorage(ElasticSearchStorage):
    index_name = "test-namedobject"
    refresh = True
    model = NamedObjectModel


@App.path(model=NamedObjectCollection, path="named_objects")
def namedobject_collection_factory(request):
    storage = NamedObjectStorage(request)
    return NamedObjectCollection(request, storage)


@App.path(model=NamedObjectModel, path="named_objects/{identifier}")
def namedobject_model_factory(request, identifier):
    col = namedobject_collection_factory(request)
    return col.get(identifier)


class BlobObjectStorage(ElasticSearchStorage):
    index_name = "test-blobobject"
    refresh = True
    model = BlobObjectModel


@App.storage(model=BlobObjectModel)
def get_blobobject_storage(model, request, blobstorage):
    return BlobObjectStorage(request, blobstorage=blobstorage)


@App.blobstorage(model=BlobObjectModel)
def get_blobobject_blobstorage(model, request):
    return FSBlobStorage(request, FSBLOB_DIR)


@App.path(model=BlobObjectCollection, path="blob_objects")
def blobobject_collection_factory(request):
    storage = request.app.get_storage(BlobObjectModel, request)
    return BlobObjectCollection(request, storage)


@App.path(model=BlobObjectModel, path="blob_objects/{identifier}")
def blobobject_model_factory(request, identifier):
    col = blobobject_collection_factory(request)
    return col.get(identifier)


def test_elasticsearchstorage(es_client):
    config = os.path.join(
        os.path.dirname(__file__), "test_elasticsearchstorage-settings.yml"
    )
    client = get_client(config)
    col = client.mfw_request.get_collection("tests.page")
    col.storage.create_index(col)
    run_jslcrud_test(client)
