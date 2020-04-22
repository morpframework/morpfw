import os
from dataclasses import dataclass
from io import BytesIO

import sqlalchemy as sa
from morpfw import Collection, Model, Schema
from morpfw.crud.blobstorage.typeblobstorage import (
    TypeBlobStorage,
    TypeBlobStoreCollection,
    TypeBlobStoreMixin,
    TypeBlobStoreModel,
    TypeBlobStoreSchema,
)
from morpfw.crud.storage.sqlstorage import GUID, Base, SQLStorage

from ..common import get_client, make_request
from .crud_common import FSBLOB_DIR, run_jslcrud_test
from .test_sqlstorage import App as BaseApp
from .test_sqlstorage import BlobObjectModel


class App(BaseApp):
    pass


@dataclass
class BlobStoreSchema(TypeBlobStoreSchema):
    pass


class BlobStoreCollection(TypeBlobStoreCollection):
    schema = BlobStoreSchema


class BlobStoreModel(TypeBlobStoreModel):
    schema = BlobStoreSchema


class BlobStore(TypeBlobStoreMixin, Base):

    __tablename__ = "morpfw_test_blobobject"


class BlobStoreStorage(SQLStorage):
    model = BlobStoreModel
    orm_model = BlobStore


@App.path(model=BlobStoreCollection, path="blobs")
def blobstore_collection_factory(request):
    storage = BlobStoreStorage(request)
    return BlobStoreCollection(request, storage)


@App.path(model=BlobStoreModel, path="blobs/{identifier}")
def blobstore_model_factory(request, identifier):
    col = blobstore_collection_factory(request)
    return col.get(identifier)


@App.blobstorage(model=BlobObjectModel)
def get_blobobject_blobstorage(model, request):
    return TypeBlobStorage(request, "blobstore")


@App.typeinfo(name="blobstore", schema=BlobStoreSchema)
def get_blobstore_typeinfo(request):
    return {
        "title": "BlobStore",
        "description": "BlobStore type",
        "schema": BlobStoreSchema,
        "collection": BlobStoreCollection,
        "collection_factory": blobstore_collection_factory,
        "model": BlobStoreModel,
        "model_factory": blobstore_model_factory,
        #
        # "collection_ui": BlobStoreCollectionUI,
        # "model_ui": BlobStoreModelUI,
        "internal": True
        #
    }


def test_sqlstorage_typeblobstorage(pgsql_db):
    config = os.path.join(
        os.path.dirname(__file__), "test_sqlstorage-typeblobstorage-settings.yml"
    )
    c = get_client(config)
    request = make_request(c.app)
    Base.metadata.create_all(bind=request.db_session.bind)
    run_jslcrud_test(c)
