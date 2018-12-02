import jsl
from .crud_common import App as BaseApp
from morpfw.crud.model import Collection, Model
from morpfw.crud.storage.sqlstorage import SQLStorage, Base, GUID
from .crud_common import get_client, run_jslcrud_test, PageCollection, PageModel
from .crud_common import ObjectCollection, ObjectModel
from .crud_common import NamedObjectCollection, NamedObjectModel
import pprint
from more.transaction import TransactionApp
from morepath.reify import reify
from morepath.request import Request

from sqlalchemy.orm import sessionmaker
from zope.sqlalchemy import register as register_session
import morpfw.crud.signals as signals
import sqlalchemy as sa
from morpfw.app import SQLApp


class App(BaseApp, SQLApp):
    pass


class Page(Base):

    __tablename__ = 'jslcrud_test_page'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    title = sa.Column(sa.String(length=1024), default='')
    body = sa.Column(sa.Text(), default='')
    value = sa.Column(sa.Integer)
    footer = sa.Column(sa.String(length=1024), default='')


class PageStorage(SQLStorage):
    model = PageModel
    orm_model = Page


@App.path(model=PageCollection, path='pages')
def collection_factory(request):
    storage = PageStorage(request)
    return PageCollection(request, storage)


@App.path(model=PageModel, path='pages/{identifier}')
def model_factory(request, identifier):
    storage = PageStorage(request)
    return storage.get(identifier)


class Object(Base):

    __tablename__ = 'jslcrud_test_object'

    objid = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    uuid = sa.Column(GUID)
    body = sa.Column(sa.String(length=1024), default='')
    created_flag = sa.Column(sa.Boolean, default=False)
    updated_flag = sa.Column(sa.Boolean, default=False)


class ObjectStorage(SQLStorage):
    model = ObjectModel
    orm_model = Object


@App.path(model=ObjectCollection, path='objects')
def object_collection_factory(request):
    storage = ObjectStorage(request)
    return ObjectCollection(request, storage)


@App.path(model=ObjectModel, path='objects/{identifier}')
def object_model_factory(request, identifier):
    storage = ObjectStorage(request)
    return storage.get(identifier)


class NamedObject(Base):

    __tablename__ = 'jslcrud_test_namedobject'

    name = sa.Column(sa.String(length=1024), primary_key=True)
    body = sa.Column(sa.String(length=1024), default='')
    created_flag = sa.Column(sa.Boolean, default=False)
    updated_flag = sa.Column(sa.Boolean, default=False)


class NamedObjectStorage(SQLStorage):
    model = NamedObjectModel
    orm_model = NamedObject


@App.path(model=NamedObjectCollection, path='named_objects')
def namedobject_collection_factory(request):
    storage = NamedObjectStorage(request)
    return NamedObjectCollection(request, storage)


@App.path(model=NamedObjectModel, path='named_objects/{identifier}')
def namedobject_model_factory(request, identifier):
    storage = NamedObjectStorage(request)
    return storage.get(identifier)


def test_sqlstorage(pgsql_db):
    c = get_client(App, config='settings-sqlalchemy.yml')
    run_jslcrud_test(c)
