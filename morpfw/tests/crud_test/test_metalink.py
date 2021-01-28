import os
import tempfile
import typing
from dataclasses import dataclass, field
from datetime import date
from urllib.parse import quote

import pytest
import rulez
from morpfw import Schema
from morpfw.app import BaseApp
from morpfw.crud import permission as crudperm
from morpfw.crud.model import Collection, Model
from morpfw.crud.statemachine.base import StateMachine
from morpfw.crud.workflow import WorkflowCollection, WorkflowModel

from ...app import SQLApp
from ...crud.storage.sqlstorage import SQLStorage
from ...sql import Base, construct_orm_model
from ..common import get_client, make_request


class App(SQLApp):
    pass


@App.permission_rule(model=Model, permission=crudperm.All)
def allow_all_model_access(identity, context, permission):
    return True


@App.permission_rule(model=Model, permission=crudperm.StateUpdate)
def allow_all_model_state_access(identity, context, permission):
    return True


@App.permission_rule(model=Collection, permission=crudperm.All)
def allow_all_collection_access(identity, context, permission):
    return True


@dataclass
class ObjectSchema(Schema):
    pass


class ObjectCollection(Collection):
    schema = ObjectSchema


class ObjectModel(Model):
    schema = ObjectSchema


@App.path(model=ObjectCollection, path="objects")
def object_collection_factory(request):
    storage = request.app.get_storage(ObjectModel, request)
    return ObjectCollection(request, storage)


@App.path(model=ObjectModel, path="objects/{identifier}")
def object_model_factory(request, identifier):
    collection = object_collection_factory(request)
    return collection.get(identifier)


@App.typeinfo(name="tests.object", schema=ObjectSchema)
def get_object_typeinfo(request):
    return {
        "title": "Object",
        "description": "Object type",
        "schema": ObjectSchema,
        "collection": ObjectCollection,
        "collection_factory": object_collection_factory,
        "model": ObjectModel,
        "model_factory": object_model_factory,
    }


class ObjectStorage(SQLStorage):
    model = ObjectModel
    orm_model = construct_orm_model(
        schema=ObjectModel.schema, metadata=Base.metadata, name="test_object"
    )


@App.storage(model=ObjectModel)
def get_object_storage(model, request, blobstorage):
    return ObjectStorage(request, blobstorage)


def test_metalink(pgsql_db):
    config = os.path.join(
        os.path.dirname(__file__), "test_metalink_sqlstorage-settings.yml"
    )
    c = get_client(config)
    request = c.mfw_request
    Base.metadata.create_all(bind=request.db_session.bind)

    app = request.app
    col = request.get_collection("tests.object")
    link = request.metalink(col)
    assert link == {
        "type": "morpfw.collection",
        "resource_type": "tests.object",
        "view_name": None,
    }
    assert request.resolve_metalink(link) == "http://localhost:5000/objects"

    obj = col.create({})
    link = request.metalink(obj)
    assert link == {
        "type": "morpfw.model",
        "resource_type": "tests.object",
        "uuid": obj.uuid,
        "view_name": None,
    }
    assert (
        request.resolve_metalink(link) == "http://localhost:5000/objects/%s" % obj.uuid
    )

    with pytest.raises(NotImplementedError):
        request.metalink(object())
