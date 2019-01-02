import jsl
from morpfw.crud.storage.memorystorage import MemoryStorage
from morpfw.crud.blobstorage.fsblobstorage import FSBlobStorage
import morpfw.crud.signals as signals
from .crud_common import get_client, run_jslcrud_test, PageCollection, PageModel
from .crud_common import ObjectCollection, ObjectModel
from .crud_common import NamedObjectCollection, NamedObjectModel
from .crud_common import App as BaseApp
from .crud_common import BlobObjectCollection, BlobObjectModel
from .crud_common import FSBLOB_DIR
from more.transaction import TransactionApp
from more.basicauth import BasicAuthIdentityPolicy


class App(BaseApp):
    pass


class PageStorage(MemoryStorage):
    model = PageModel


@App.path(model=PageCollection, path='pages')
def collection_factory(request):
    storage = PageStorage(request)
    return PageCollection(request, storage)


@App.path(model=PageModel, path='pages/{identifier}')
def model_factory(request, identifier):
    storage = PageStorage(request)
    return storage.get(identifier)


class ObjectStorage(MemoryStorage):
    incremental_id = True
    incremental_column = 'id'
    model = ObjectModel


@App.path(model=ObjectCollection, path='objects')
def object_collection_factory(request):
    storage = ObjectStorage(request)
    return ObjectCollection(request, storage)


@App.path(model=ObjectModel, path='objects/{identifier}')
def object_model_factory(request, identifier):
    storage = ObjectStorage(request)
    return storage.get(identifier)


class NamedObjectStorage(MemoryStorage):
    model = NamedObjectModel


@App.path(model=NamedObjectCollection, path='named_objects')
def namedobject_collection_factory(request):
    storage = NamedObjectStorage(request)
    return NamedObjectCollection(request, storage)


@App.path(model=NamedObjectModel, path='named_objects/{identifier}')
def namedobject_model_factory(request, identifier):
    storage = NamedObjectStorage(request)
    o = storage.get(identifier)
    return o


class BlobObjectStorage(MemoryStorage):
    model = BlobObjectModel


@App.storage(model=BlobObjectModel)
def get_blobobject_storage(model, request, blobstorage):
    return BlobObjectStorage(request, blobstorage=blobstorage)


@App.blobstorage(model=BlobObjectModel)
def get_blobobject_blobstorage(model, request):
    return FSBlobStorage(request, FSBLOB_DIR)


@App.path(model=BlobObjectCollection, path='blob_objects')
def blobobject_collection_factory(request):
    storage = request.app.get_storage(BlobObjectModel, request)
    return BlobObjectCollection(request, storage)


@App.path(model=BlobObjectModel, path='blob_objects/{identifier}')
def blobobject_model_factory(request, identifier):
    storage = request.app.get_storage(BlobObjectModel, request)
    return storage.get(identifier)


def test_memorystorage():
    client = get_client(App)
    run_jslcrud_test(client, skip_aggregate=True)
