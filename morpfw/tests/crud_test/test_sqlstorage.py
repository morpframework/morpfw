import os
import pprint

import jsl
import morpfw.crud.signals as signals
import sqlalchemy as sa
import sqlalchemy_jsonfield as sajson
from more.transaction import TransactionApp
from morepath.reify import reify
from morepath.request import Request
from morpfw.app import SQLApp
from morpfw.crud.blobstorage.fsblobstorage import FSBlobStorage
from morpfw.crud.model import Collection, Model
from morpfw.crud.storage.sqlstorage import GUID, Base, SQLStorage
from sqlalchemy.orm import sessionmaker
from zope.sqlalchemy import register as register_session

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


class App(BaseApp, SQLApp):
    pass


class Page(Base):

    __tablename__ = "jslcrud_test_page"

    title = sa.Column(sa.String(length=1024), default="")
    body = sa.Column(sa.Text(), default="")
    publish_date = sa.Column(sa.Date())
    publish_datetime = sa.Column(sa.DateTime(timezone=True))
    value = sa.Column(sa.Integer)
    footer = sa.Column(sa.String(length=1024), default="")
    computed_title = sa.Column(sa.String(length=1024), default="")

class PageStorage(SQLStorage):
    model = PageModel
    orm_model = Page


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


class Object(Base):

    __tablename__ = "jslcrud_test_object"

    body = sa.Column(sa.String(length=1024), default="")
    created_flag = sa.Column(sa.Boolean, default=False)
    updated_flag = sa.Column(sa.Boolean, default=False)
    attrs = sa.Column(sajson.JSONField)


class ObjectStorage(SQLStorage):
    model = ObjectModel
    orm_model = Object


@App.path(model=ObjectCollection, path="objects")
def object_collection_factory(request):
    storage = ObjectStorage(request)
    return ObjectCollection(request, storage)


@App.path(model=ObjectModel, path="objects/{identifier}")
def object_model_factory(request, identifier):
    col = object_collection_factory(request)
    return col.get(identifier)


class NamedObject(Base):

    __tablename__ = "jslcrud_test_namedobject"

    name = sa.Column(sa.String(length=1024), default="")
    body = sa.Column(sa.String(length=1024), default="")
    created_flag = sa.Column(sa.Boolean, default=False)
    updated_flag = sa.Column(sa.Boolean, default=False)


class NamedObjectStorage(SQLStorage):
    model = NamedObjectModel
    orm_model = NamedObject


@App.path(model=NamedObjectCollection, path="named_objects")
def namedobject_collection_factory(request):
    storage = NamedObjectStorage(request)
    return NamedObjectCollection(request, storage)


@App.path(model=NamedObjectModel, path="named_objects/{identifier}")
def namedobject_model_factory(request, identifier):
    col = namedobject_collection_factory(request)
    return col.get(identifier)


class BlobObject(Base):

    __tablename__ = "jslcrud_test_blobobject"

    blobs = sa.Column(sajson.JSONField())


class BlobObjectStorage(SQLStorage):
    model = BlobObjectModel
    orm_model = BlobObject


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


def test_sqlstorage(pgsql_db):
    config = os.path.join(os.path.dirname(__file__), "test_sqlstorage-settings.yml")
    c = get_client(config)
    request = make_request(c.app)
    Base.metadata.create_all(bind=request.db_session.bind)
    run_jslcrud_test(c)
