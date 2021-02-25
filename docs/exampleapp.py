import typing
from dataclasses import dataclass, field

import morpfw
import morpfw.sql
import sqlalchemy as sa
from morpfw.authz.pas import DefaultAuthzPolicy
from morpfw.crud import permission as crudperm
from morpfw.permission import All


class AppRoot(object):
    def __init__(self, request):
        self.request = request


class App(DefaultAuthzPolicy, morpfw.SQLApp):
    pass


@App.path(model=AppRoot, path="/")
def get_approot(request):
    return AppRoot(request)


@App.permission_rule(model=AppRoot, permission=All)
def allow_all(identity, context, permission):
    """ Default permission rule, allow all """
    return True


@App.json(model=AppRoot)
def index(context, request):
    return {"message": "Hello World"}


@dataclass
class PageSchema(morpfw.Schema):

    body: typing.Optional[str] = field(default=None, metadata={"title": "Body"})
    value: typing.Optional[int] = field(default=0, metadata={"title": "Value"})


class PageCollection(morpfw.Collection):
    schema = PageSchema


class PageModel(morpfw.Model):
    schema = PageSchema

    blob_fields = ['attachment']

# SQLALchemy model
class Page(morpfw.sql.Base):

    __tablename__ = "test_page"

    body = sa.Column(sa.Text())
    value = sa.Collection(sa.Integer())


class PageStorage(morpfw.SQLStorage):
    model = PageModel
    orm_model = Page


@App.storage(model=PageModel)
def get_storage(model, request, blobstorage):
    return PageStorage(request, blobstorage=blobstorage)


@App.path(model=PageCollection, path="/pages")
def get_collection(request):
    storage = request.app.get_storage(PageModel, request)
    return PageCollection(request, storage)


@App.path(model=PageModel, path="/pages/{identifier}")
def get_model(request, identifier):
    col = get_collection(request)
    return col.get(identifier)


class PageStateMachine(morpfw.StateMachine):

    states = ["new", "pending", "approved"]
    transitions = [
        {"trigger": "approve", "source": ["new", "pending"], "dest": "approved"},
        {"trigger": "submit", "source": "new", "dest": "pending"},
    ]


@App.statemachine(model=PageModel)
def get_pagemodel_statemachine(context):
    return PageStateMachine(context)


@App.permission_rule(model=PageCollection, permission=All)
def allow_collection_all(identity, context, permission):
    """ Default permission rule, allow all """
    return True


@App.permission_rule(model=PageModel, permission=All)
def allow_model_all(identity, context, permission):
    """ Default permission rule, allow all """
    return True


@App.typeinfo(name="test.page", schema=PageSchema)
def get_typeinfo(request):
    return {
        "title": "Test Page",
        "description": "",
        "schema": PageSchema,
        "collection": PageCollection,
        "collection_factory": get_collection,
        "model": PageModel,
        "model_factory": get_model,
    }
