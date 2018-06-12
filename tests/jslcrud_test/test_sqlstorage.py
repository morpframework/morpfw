import jsl
from jslcrud_common import App as BaseApp
from morpfw.jslcrud.model import Collection, Model
from morpfw.jslcrud.storage.sqlstorage import SQLStorage, Base, GUID
from jslcrud_common import get_client, run_jslcrud_test, PageCollection, PageModel
from jslcrud_common import ObjectCollection, ObjectModel
from jslcrud_common import NamedObjectCollection, NamedObjectModel
import pprint
from more.transaction import TransactionApp
from morepath.reify import reify
from morepath.request import Request
from more.basicauth import BasicAuthIdentityPolicy
from sqlalchemy.orm import sessionmaker
from zope.sqlalchemy import register as register_session
import morpfw.jslcrud.signals as signals
import sqlalchemy as sa


Session = sessionmaker()
register_session(Session)


class DBSessionRequest(Request):

    @reify
    def db_session(self):
        return Session()


class App(BaseApp, TransactionApp):

    request_class = DBSessionRequest


@App.identity_policy()
def get_identity_policy():
    return BasicAuthIdentityPolicy()


@App.verify_identity()
def verify_identity(identity):
    if identity.userid == 'admin' and identity.password == 'admin':
        return True
    return False


class Page(Base):

    __tablename__ = 'jslcrud_test_page'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    uuid = sa.Column(sa.String(length=1024), default='')
    title = sa.Column(sa.String(length=1024), default='')
    body = sa.Column(sa.Text(), default='')
    value = sa.Column(sa.Integer)
    footer = sa.Column(sa.String(length=1024), default='')
    created = sa.Column(sa.DateTime)
    modified = sa.Column(sa.DateTime)
    state = sa.Column(sa.String)


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

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
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
    created = sa.Column(sa.Boolean, default=False)
    updated = sa.Column(sa.Boolean, default=False)


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
    engine = sa.create_engine(
        'postgresql://postgres@localhost:45678/morp_tests')
    Session.configure(bind=engine)
    Base.metadata.create_all(engine)
    run_jslcrud_test(App)
