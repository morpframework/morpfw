import os
import typing
from dataclasses import dataclass

import morpfw
import sqlalchemy as sa
from morpfw import sql as morpsql
from morpfw.crud import Collection, Model
from morpfw.crud import permission as crudperm
from morpfw.crud.schema import Schema

from .common import get_client, make_request


class App(morpfw.SQLApp):
    pass


@App.permission_rule(model=Model, permission=crudperm.All)
def allow_all_model_access(identity, context, permission):
    return True


@App.permission_rule(model=Model, permission=crudperm.StateUpdate)
def allow_statemachine(identity, context, permission):
    return True


@App.permission_rule(model=Collection, permission=crudperm.All)
def allow_all_collection_access(identity, context, permission):
    return True


class Page(morpsql.Base):
    __tablename__ = "test_page"

    title = sa.Column(sa.String(length=1024))
    body = sa.Column(sa.Text)


@dataclass
class PageSchema(Schema):
    title: typing.Optional[str] = None
    body: typing.Optional[str] = None


@App.identifierfield(schema=PageSchema)
def page_schema_identifier(schema):
    return "uuid"


class PageCollection(morpfw.Collection):
    schema = PageSchema


class PageModel(morpfw.Model):
    schema = PageSchema


class PageStorage(morpfw.SQLStorage):
    model = PageModel
    orm_model = Page


@App.path(model=PageCollection, path="/")
def get_pagecollection(request):
    storage = PageStorage(request)
    return PageCollection(request, storage)


@App.path(model=PageModel, path="/{identifier}")
def get_page(request, identifier):
    col = get_pagecollection(request)
    return col.get(identifier)


def test_morp_framework(pgsql_db):
    c = get_client(os.path.join(os.path.dirname(__file__), "test_sqlapp-settings.yml"))
    req = make_request(c.app)
    morpsql.Base.metadata.create_all(bind=req.db_session.bind)
    r = c.get("/")

    assert len(r.json["schema"]["properties"]) == 11

    r = c.post_json("/", {"title": "Hello world", "body": "Lorem ipsum"})

    assert r.json["links"][0]["href"].startswith("http://localhost/")
    assert r.json["data"]["title"] == "Hello world"
    assert r.json["data"]["body"] == "Lorem ipsum"

    page_url = r.json["links"][0]["href"]
    r = c.get(page_url)

    assert r.json["data"]["title"] == "Hello world"

    delete_link = r.json["links"][2]
    assert delete_link["method"] == "DELETE"

    r = c.delete(delete_link["href"])

    r = c.get(page_url, expect_errors=True)

    assert r.status_code == 404
