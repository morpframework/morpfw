import os
import time
import typing
import uuid
from dataclasses import dataclass

import jsl
import morepath
import morpfw
import pytest
import sqlalchemy as sa
from morpfw import sql as morpsql
from morpfw.crud import Collection, Model
from morpfw.crud import permission as crudperm
from morpfw.crud.schema import Schema

from .common import get_client, make_request, start_scheduler, start_worker
from .test_sqlapp import Page


class App(morpfw.SQLApp):
    pass


@App.permission_rule(model=Model, permission=crudperm.All)
def allow_all_model_access(identity, context, permission):
    return True


@App.permission_rule(model=Collection, permission=crudperm.All)
def allow_all_collection_access(identity, context, permission):
    return True


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
    storage = PageStorage(request)
    collection = PageCollection(request, storage)
    return storage.get(collection, identifier)


@App.periodic(name="test-tick", seconds=1)
def tick(request_options):
    request_options["scan"] = False
    morepath.scan(morpfw)
    with morpfw.request_factory(**request_options) as request:
        collection = get_pagecollection(request)
        collection.create({"title": "Hello", "body": "World"})
    print("tick")


def test_scheduler(pgsql_db, pika_connection_channel):
    config = os.path.join(
        os.path.dirname(__file__), "test_workerscheduler-settings.yml"
    )
    c = get_client(config)
    request = make_request(c.app)
    morpsql.Base.metadata.create_all(bind=request.db_session.bind)

    r = c.get("/+search")

    assert len(r.json["results"]) == 0

    worker_proc = start_worker(c.app)
    time.sleep(2)
    sched_proc = start_scheduler(c.app)
    time.sleep(2)

    r = c.get("/+search")

    assert len(r.json["results"]) > 0

    sched_proc.terminate()
    time.sleep(2)
    worker_proc.terminate()
    time.sleep(5)
