import os

import jsl
import morpfw.crud.signals as signals
from inverter import dc2pgsqla
from more.basicauth import BasicAuthIdentityPolicy
from more.transaction import TransactionApp
from morpfw.app import SQLApp
from morpfw.crud.blobstorage.fsblobstorage import FSBlobStorage
from morpfw.crud.storage.pgsqlstorage import PgSQLStorage
from sqlalchemy import MetaData

from ..common import get_client, make_request
from .crud_common import FSBLOB_DIR
from .crud_common import App as BaseApp
from .crud_common import (
    BlobObjectCollection,
    BlobObjectModel,
    NamedObjectCollection,
    NamedObjectModel,
    ObjectCollection,
    ObjectModel,
    PageCollection,
    PageModel,
    PageSchema,
    run_jslcrud_test,
)

db_meta = MetaData()


class App(BaseApp, SQLApp):
    pass


class PageStorage(PgSQLStorage):
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


class ObjectStorage(PgSQLStorage):
    model = ObjectModel


@App.path(model=ObjectCollection, path="objects")
def object_collection_factory(request):
    storage = ObjectStorage(request)
    return ObjectCollection(request, storage)


@App.path(model=ObjectModel, path="objects/{identifier}")
def object_model_factory(request, identifier):
    col = object_collection_factory(request)
    return col.get(identifier)


class NamedObjectStorage(PgSQLStorage):
    model = NamedObjectModel


@App.path(model=NamedObjectCollection, path="named_objects")
def namedobject_collection_factory(request):
    storage = NamedObjectStorage(request)
    return NamedObjectCollection(request, storage)


@App.path(model=NamedObjectModel, path="named_objects/{identifier}")
def namedobject_model_factory(request, identifier):
    col = namedobject_collection_factory(request)
    return col.get(identifier)


class BlobObjectStorage(PgSQLStorage):
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


def test_pgsqlstorage(pgsql_db):
    config = os.path.join(os.path.dirname(__file__), "test_pgsqlstorage-settings.yml")
    c = get_client(config)
    request = make_request(c.app)

    # create tables

    db_meta.bind = request.db_session.get_bind()
    for model in [PageModel, ObjectModel, NamedObjectModel, BlobObjectModel]:
        dc2pgsqla.convert(model.schema, db_meta)
    db_meta.create_all()

    run_jslcrud_test(c)
