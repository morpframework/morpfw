import typing
from dataclasses import dataclass, field

import morpfw
import morpfw.sql
import sqlalchemy as sa


@dataclass
class PageSchema(morpfw.Schema):

    title: typing.Optional[str] = field(default=None, metadata={"title": "Title"})
    body: typing.Optional[str] = field(default=None, metadata={"title": "Body"})


class PageCollection(morpfw.Collection):
    schema = PageSchema


class PageModel(morpfw.Model):
    schema = PageSchema


# SQLALchemy model
class Page(morpfw.sql.Base):

    __tablename__ = "test_page"

    title = sa.Column(sa.String(length=1024))
    body = sa.Column(sa.Text())


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
