import morpfw
import sqlalchemy as sa
from morpfw.crud import permission as crudperm
import typing
from .app import App


class PageSchema(morpfw.Schema):
    body: typing.Optional[str] = None


class PageCollection(morpfw.Collection):
    schema = PageSchema


class PageModel(morpfw.Model):
    schema = PageSchema


class Page(morpfw.SQLBase):
    __tablename__ = 'test_page'

    body = sa.Column(sa.String(length=1024))


class PageStorage(morpfw.SQLStorage):
    model = PageModel
    orm_model = Page


@App.path(model=PageCollection, path='pages')
def get_collection(request):
    storage = PageStorage(request)
    return PageCollection(request, storage)


@App.path(model=PageModel, path='pages/{identifier}')
def get_model(request, identifier):
    collection = get_collection(request)
    return collection.get(identifier)


@App.permission_rule(model=PageModel, permission=crudperm.All)
def allow_model(identity, context, permission):
    return True


@App.permission_rule(model=PageCollection, permission=crudperm.All)
def allow_collection(identity, context, permission):
    return True
