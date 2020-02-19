import os

import jsl
import morpfw.crud.signals as signals
from more.basicauth import BasicAuthIdentityPolicy
from more.transaction import TransactionApp
from morpfw.crud.blobstorage.fsblobstorage import FSBlobStorage
from morpfw.crud.storage.memorystorage import MemoryStorage

from ..common import get_client
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


class App(BaseApp):
    pass


class PageStorage(MemoryStorage):
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


class ObjectStorage(MemoryStorage):
    incremental_id = True
    incremental_column = "id"
    model = ObjectModel


@App.path(model=ObjectCollection, path="objects")
def object_collection_factory(request):
    storage = ObjectStorage(request)
    return ObjectCollection(request, storage)


@App.path(model=ObjectModel, path="objects/{identifier}")
def object_model_factory(request, identifier):
    col = object_collection_factory(request)
    return col.get(identifier)


class NamedObjectStorage(MemoryStorage):
    model = NamedObjectModel


@App.path(model=NamedObjectCollection, path="named_objects")
def namedobject_collection_factory(request):
    storage = NamedObjectStorage(request)
    return NamedObjectCollection(request, storage)


@App.path(model=NamedObjectModel, path="named_objects/{identifier}")
def namedobject_model_factory(request, identifier):
    col = namedobject_collection_factory(request)
    return col.get(identifier)


class BlobObjectStorage(MemoryStorage):
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


def test_memorystorage():
    config = os.path.join(os.path.dirname(__file__), "test_memorystorage-settings.yml")
    client = get_client(config)
    run_jslcrud_test(client, skip_aggregate=True)
