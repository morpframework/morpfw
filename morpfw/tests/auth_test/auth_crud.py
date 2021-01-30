from dataclasses import dataclass, field

from morpfw import Collection, Model, Schema
from morpfw.app import BaseApp
from morpfw.authz.pas import DefaultAuthzPolicy

from .test_auth import login, logout


class App(BaseApp, DefaultAuthzPolicy):
    pass


@dataclass
class Object1Schema(Schema):

    title: str = field(
        default="", metadata={"format": "text"},
    )


class Object1Collection(Collection):
    schema = Object1Schema


class Object1Model(Model):
    schema = Object1Schema


@App.path(model=Object1Collection, path="object1")
def object1_collection_factory(request):
    storage = request.app.get_storage(Object1Model, request)
    return Object1Collection(request, storage)


@App.path(model=Object1Model, path="object1/{identifier}")
def object1_model_factory(request, identifier):
    collection = object1_collection_factory(request)
    return collection.get(identifier)


@App.typeinfo(name="tests.object1", schema=Object1Schema)
def get_object1_typeinfo(request):
    return {
        "title": "Object1",
        "description": "Object1 type",
        "schema": Object1Schema,
        "collection": Object1Collection,
        "collection_factory": object1_collection_factory,
        "model": Object1Model,
        "model_factory": object1_model_factory,
    }


@dataclass
class Object2Schema(Schema):

    title: str = field(
        default="", metadata={"format": "text"},
    )


class Object2Collection(Collection):
    schema = Object2Schema


class Object2Model(Model):
    schema = Object2Schema


@App.path(model=Object2Collection, path="object2")
def object2_collection_factory(request):
    storage = request.app.get_storage(Object2Model, request)
    return Object2Collection(request, storage)


@App.path(model=Object2Model, path="object2/{identifier}")
def object2_model_factory(request, identifier):
    collection = object2_collection_factory(request)
    return collection.get(identifier)


@App.typeinfo(name="tests.object2", schema=Object2Schema)
def get_object2_typeinfo(request):
    return {
        "title": "Object2",
        "description": "Object2 type",
        "schema": Object2Schema,
        "collection": Object2Collection,
        "collection_factory": object2_collection_factory,
        "model": Object2Model,
        "model_factory": object2_model_factory,
    }


def run_test(c):

    login(c, "admin")

    r = c.post_json(
        "/user/+register",
        {
            "username": "user1",
            "email": "user1@localhost.com",
            "timezone": "UTC",
            "password": "password",
            "password_validate": "password",
        },
    )

    login(c, "user1")

    r = c.get("/object1/+search")

    r = c.post_json("/object1/", {"title": "Hello"})

    obj_uuid = r.json["data"]["uuid"]

    r = c.get("/object1/%s" % obj_uuid)

    r = c.patch_json("/object1/%s" % obj_uuid, {"title": "World"})

    r = c.get("/object1/%s" % obj_uuid)

    r = c.delete("/object1/%s" % obj_uuid)

    r = c.get("/object2/")

    r = c.get("/object2/+search")

    r = c.post_json("/object2/", {"title": "Hello"}, expect_errors=True)

    assert r.status_code == 403

    login(c, "admin")

    r = c.post_json("/object2/", {"title": "Hello"})

    obj2_uuid = r.json["data"]["uuid"]

    login(c, "user1")

    r = c.get("/object2/%s" % obj2_uuid, expect_errors=True)

    assert r.status_code == 403

    r = c.patch_json("/object2/%s" % obj2_uuid, {"title": "World"}, expect_errors=True)

    assert r.status_code == 403

    r = c.delete("/object2/%s" % obj2_uuid, expect_errors=True)

    assert r.status_code == 403
