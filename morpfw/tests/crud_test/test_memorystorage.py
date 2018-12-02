import jsl
from morpfw.crud.storage.memorystorage import MemoryStorage
import morpfw.crud.signals as signals
from .crud_common import get_client, run_jslcrud_test, PageCollection, PageModel
from .crud_common import ObjectCollection, ObjectModel
from .crud_common import NamedObjectCollection, NamedObjectModel
from .crud_common import App as BaseApp
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


def test_memorystorage():
    client = get_client(App)
    run_jslcrud_test(client, skip_aggregate=True)
