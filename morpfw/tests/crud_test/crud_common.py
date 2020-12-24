import json
import os
import shutil
import tempfile
import typing
from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import uuid4

import jsl
import morepath
import morpfw.crud.signals as signals
import pytz
import yaml
from more.basicauth import BasicAuthIdentityPolicy
from morpfw.app import BaseApp
from morpfw.authn.base import AuthnPolicy as BaseAuthnPolicy
from morpfw.crud import permission as crudperm
from morpfw.crud.model import Collection, Model
from morpfw.crud.schema import BaseSchema, Schema
from morpfw.crud.statemachine.base import StateMachine
from morpfw.crud.xattrprovider import FieldXattrProvider
from morpfw.crud.xattrprovider.base import XattrProvider
from morpfw.identity import Identity
from morpfw.interfaces import ISchema
from morpfw.main import create_app
from webtest import TestApp as Client

FSBLOB_DIR = tempfile.mkdtemp()

epoch = date(1970, 1, 1)


class App(BaseApp):
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


def validate_body(request, schema, data, mode=None, **kw):
    if not isinstance(data["body"], str):
        return

    if data["body"].lower() == "invalid":
        return {"field": "body", "message": "Body must not be 'invalid'"}


@dataclass
class PageSchema(Schema):

    title: str = field(
        default="", metadata={"format": "text",},
    )
    body: str = ""
    publish_date: typing.Optional[date] = None
    publish_datetime: typing.Optional[datetime] = None
    value: typing.Optional[int] = None
    footer: typing.Optional[str] = ""
    computed_title: typing.Optional[str] = field(
        default=None, metadata={"compute_value": lambda req, d, m: "computed title"}
    )


@App.formvalidators(schema=PageSchema)
def page_formvalidators(schema):
    return [validate_body]


class PageCollection(Collection):
    schema = PageSchema


class PageModel(Model):
    schema = PageSchema


@dataclass
class ObjectSchema(Schema):

    body: str = ""
    created_flag: typing.Optional[bool] = False
    updated_flag: typing.Optional[bool] = False
    attrs: typing.Optional[dict] = field(default_factory=dict)


class ObjectCollection(Collection):
    schema = ObjectSchema


class ObjectModel(Model):
    schema = ObjectSchema


@App.subscribe(signal=signals.OBJECT_CREATED, model=ObjectModel)
def object_created(app, request, obj, signal):
    obj.data["created_flag"] = True


@App.subscribe(signal=signals.OBJECT_UPDATED, model=ObjectModel)
def object_updated(app, request, obj, signal):
    obj.data["updated_flag"] = True


@dataclass
class ObjectXattrSchema(BaseSchema):

    message: typing.Optional[str] = None
    message_date: typing.Optional[date] = None


class ObjectXattrProvider(FieldXattrProvider):

    schema = ObjectXattrSchema


@App.xattrprovider(model=ObjectModel)
def get_objectmodel_xattrprovider(context):
    return ObjectXattrProvider(context)


class PageStateMachine(StateMachine):

    states = ["new", "pending", "approved"]
    transitions = [
        {"trigger": "approve", "source": ["new", "pending"], "dest": "approved"},
        {"trigger": "submit", "source": "new", "dest": "pending"},
    ]


@App.statemachine(model=PageModel)
def get_pagemodel_statemachine(context):
    return PageStateMachine(context)


@dataclass
class NamedObjectSchema(Schema):

    name: typing.Optional[str] = None
    body: typing.Optional[str] = ""
    created_flag: typing.Optional[bool] = False
    updated_flag: typing.Optional[bool] = False


@App.identifierfield(schema=NamedObjectSchema)
def namedobject_identifierfield(schema):
    return "name"


@App.default_identifier(schema=NamedObjectSchema)
def namedobject_default_identifier(schema, obj, request):
    return obj["name"]


class NamedObjectCollection(Collection):
    schema = NamedObjectSchema


@App.json(model=NamedObjectCollection, name="get_uuid")
def get_object_by_uuid(context, request):
    uuid = request.GET.get("uuid")
    return context.get_by_uuid(uuid).json()


class NamedObjectModel(Model):
    schema = NamedObjectSchema


class BlobObjectSchema(Schema):
    pass


class BlobObjectCollection(Collection):
    schema = BlobObjectSchema


class BlobObjectModel(Model):
    schema = BlobObjectSchema

    blob_fields = ["blobfile"]


_USERUIDS = {}


class IdentityPolicy(BasicAuthIdentityPolicy):
    def identify(self, request):
        identity = super().identify(request)
        if isinstance(identity, morepath.Identity):
            uuid = _USERUIDS.get(identity.userid, None)
            if not uuid:
                uuid = uuid4().hex
                _USERUIDS[identity.userid] = uuid

            return Identity(
                request=request,
                userid=uuid,
                username=identity.userid,
                password=identity.password,
            )
        return identity


class AuthnPolicy(BaseAuthnPolicy):
    def get_identity_policy(self, settings):
        return IdentityPolicy()

    def verify_identity(self, app, identity):
        if identity.username == "admin" and identity.password == "admin":
            return True
        return False


def run_jslcrud_test(c, skip_aggregate=False):

    c.authorization = ("Basic", ("admin", "admin"))

    # test loading the model details and schema
    r = c.get("/pages")

    assert r.json["schema"]["type"] == "object"

    if not skip_aggregate:
        # test simple count
        r = c.get("/pages/+aggregate", {"group": ("count:count(uuid)")},)
        assert r.json[0]["count"] == 0

    # lets try creating an entry
    publish_date = (date(2019, 1, 1) - epoch).days
    publish_datetime = int(
        datetime(2019, 1, 1, 1, 1, tzinfo=pytz.UTC).timestamp() * 1000
    )
    r = c.post_json(
        "/pages/",
        {
            "title": "Hello",
            "body": "World",
            "publish_date": publish_date,
            "publish_datetime": publish_datetime,
        },
    )

    assert r.json["data"]["title"] == "Hello"
    assert r.json["data"]["publish_date"] == publish_date
    assert r.json["data"]["publish_datetime"] == publish_datetime
    assert r.json["data"]["computed_title"] == "computed title"
    uuid = r.json["data"]["uuid"]
    assert uuid
    assert len(uuid) == 32

    r = c.get("/pages/%s" % uuid)

    assert r.json["data"]["title"] == "Hello"
    assert r.json["data"]["state"] == "new"

    # lets see if the entry appears in listing

    for i in range(10):
        r = c.post_json(
            "/pages/", {"title": "page%s" % i, "body": "page%sbody" % i, "value": i}
        )

    if not skip_aggregate:
        r = c.get(
            "/pages/+aggregate",
            {
                "group": (
                    "count:count(uuid), year:year(created), month:month(created),"
                    "day:day(created), sum:sum(value), avg:avg(value)"
                )
            },
        )

        now = datetime.utcnow()
        assert r.json[0]["year"] == now.year
        assert r.json[0]["month"] == now.month
        assert r.json[0]["day"] == now.day
        assert r.json[0]["sum"] == 45
        assert r.json[0]["count"] == 11
        assert r.json[0]["avg"] == 4.5

        r = c.get("/pages/+aggregate", {"group": ("created:created"), "limit": 1},)

        assert len(r.json) == 1

    r = c.get("/pages/+search", {"q": 'title in ["Hello","something"]'})

    assert r.json["results"][0]["data"]["title"] == "Hello"

    r = c.get("/pages/+search")

    assert "Hello" in [i["data"]["title"] for i in r.json["results"]]

    r = c.get("/pages/+search", {"select": "$.title", "q": 'title in ["Hello"]'})

    assert r.json["results"] == [["Hello"]]

    r = c.get(
        "/pages/+search", {"select": "$.[title, body]", "q": 'title in ["Hello"]'}
    )

    assert r.json["results"] == [["Hello", "World"]]

    r = c.get("/pages/+search", {"order_by": "title"})

    assert list([i["data"]["title"] for i in r.json["results"]]) == (
        ["Hello"] + ["page%s" % i for i in range(10)]
    )

    r = c.get("/pages/+search", {"order_by": "title:desc"})

    assert list([i["data"]["title"] for i in r.json["results"]]) == (
        ["page%s" % i for i in range(9, -1, -1)] + ["Hello"]
    )

    r = c.get("/pages/+search", {"order_by": "title", "limit": 5})

    assert list([i["data"]["title"] for i in r.json["results"]]) == (
        ["Hello"] + ["page%s" % i for i in range(4)]
    )

    r = c.get("/pages/+search", {"order_by": "title", "offset": 1})

    assert list([i["data"]["title"] for i in r.json["results"]]) == (
        ["page%s" % i for i in range(10)]
    )

    r = c.get("/pages/+search", {"order_by": "title", "offset": 1, "limit": 5})

    assert list([i["data"]["title"] for i in r.json["results"]]) == (
        ["page%s" % i for i in range(5)]
    )

    # lets create another with wrong invalid values
    r = c.post_json(
        "/pages/", {"title": "page2", "body": 123, "footer": 123}, expect_errors=True
    )

    assert r.json["status"] == "error"
    assert len(r.json["field_errors"]) == 2
    assert len(r.json["form_errors"]) == 0

    r = c.post_json(
        "/pages/",
        {"title": "page2", "body": "valid", "footer": 123},
        expect_errors=True,
    )

    assert r.json["status"] == "error"
    assert len(r.json["field_errors"]) == 1

    r = c.post_json(
        "/pages/",
        {"title": "page2", "body": "invalid", "footer": "footer"},
        expect_errors=True,
    )

    assert r.json["status"] == "error"
    assert len(r.json["field_errors"]) == 1

    # lets update the entry
    r = c.patch_json("/pages/%s" % uuid, {"body": "newbody"})

    assert r.json["status"] == "success"

    r = c.get("/pages/%s" % uuid)

    assert r.json["data"]["body"] == "newbody"

    # lets approve the page

    r = c.post_json("/pages/%s/+statemachine" % uuid, {"transition": "approve"})

    r = c.get("/pages/%s" % uuid)

    assert r.json["data"]["state"] == "approved"

    # it cant be approved twice

    r = c.post_json(
        "/pages/%s/+statemachine" % uuid, {"transition": "approve"}, expect_errors=True
    )

    assert r.status_code == 422

    r = c.patch_json("/pages/%s" % uuid, {"body": "invalid"}, expect_errors=True)

    assert r.json["status"] == "error"

    # lets delete the entry

    r = c.get("/pages/+search")

    assert len(r.json["results"]) == 11

    r = c.delete("/pages/%s" % uuid)

    assert r.json["status"] == "success"

    r = c.get("/pages/%s" % uuid, expect_errors=True)

    r = c.get("/pages/+search")

    assert len(r.json["results"]) == 10

    r = c.get("/objects")

    assert r.json

    r = c.post_json("/objects/", {"body": "hello"})

    assert r.json["data"]["body"] == "hello"
    assert r.json["data"]["created_flag"] is True
    assert r.json["data"]["created"]
    assert r.json["data"]["creator"] == _USERUIDS["admin"]

    obj_link = r.json["links"][0]["href"]
    obj_xattr_link = obj_link + "/+xattr"
    r = c.get(obj_xattr_link)

    assert r.json == {}

    r = c.get(obj_link)

    assert (
        r.json["data"].get("xattrs", None) is None
        or r.json["data"].get("xattrs", None) == {}
    )

    r = c.get(obj_link + "/+xattr-schema")

    assert r.json["schema"]["$schema"]

    r = c.patch_json(
        obj_xattr_link,
        {"message": "hello world", "message_date": "201"},
        expect_errors=True,
    )

    assert r.status_code == 422

    message_date = (date(2019, 1, 1) - epoch).days
    r = c.patch_json(
        obj_xattr_link, {"message": "hello world", "message_date": message_date},
    )

    assert r.status_code == 200

    r = c.get(obj_xattr_link)

    assert r.json == {"message": "hello world", "message_date": message_date}

    r = c.get(obj_link)
    assert r.json["data"]["xattrs"] == {
        "message": "hello world",
        "message_date": message_date,
    }

    r = c.patch_json(obj_xattr_link, {"message": "hello world", "anotherkey": "boo"},)

    assert r.status_code == 200

    r = c.patch_json(obj_link, {"xattrs": {"message": "invalid"}}, expect_errors=True)

    assert r.status_code == 422

    # object output valiidation should bail out with additional xattr
    r = c.get(obj_link)

    assert r.status_code == 200

    # test creation of named object
    r = c.post_json("/named_objects/", {"name": "obj1", "body": "hello"})

    r = c.get("/named_objects/obj1")

    assert r.json["data"]["name"] == "obj1"
    uuid = r.json["data"]["uuid"]
    original_object = r.json["data"]
    r = c.get("/named_objects/+get_uuid?uuid=%s" % uuid)
    object_by_uuid = r.json["data"]
    assert original_object == object_by_uuid

    # duplicate should fail
    r = c.post_json(
        "/named_objects/", {"name": "obj1", "body": "hello"}, expect_errors=True
    )

    assert r.status_code == 422

    # catch issue with ':' in name

    r = c.post_json("/named_objects/", {"name": "object:obj2", "body": "hello"})

    r = c.get("/named_objects/object:obj2")

    assert r.json["data"]["name"] == "object:obj2"

    r = c.get("/named_objects/object:obj2?select=$.[body]")

    assert r.json == ["hello"]

    # catch issue with ' ' in name

    r = c.post_json("/named_objects/", {"name": "object obj2", "body": "hello"})

    r = c.get("/named_objects/object%20obj2")

    assert r.json["data"]["name"] == "object obj2"

    r = c.patch_json("/named_objects/object%20obj2", {"body": "hello1"})

    assert r.status_code == 200

    # blob upload test

    r = c.post_json("/blob_objects", {})

    bloburl = r.json["links"][0]["href"]

    r = c.get(bloburl)

    testimg = os.path.join(os.path.dirname(__file__), "testimg.png")

    r = c.post(bloburl + "/+blobs?field=blobfile", upload_files=[("upload", testimg)])

    assert r.status_code == 200

    r = c.get(bloburl)

    assert r.json["data"]["blobs"]["blobfile"]

    r = c.get(bloburl + "/+blobs?field=blobfile")

    with open(testimg, "rb") as ti:
        assert r.body == ti.read()

    assert r.headers.get("Content-Type") == "image/png"

    r = c.delete(bloburl + "/+blobs?field=blobfile")

    assert r.status_code == 200

    r = c.get(bloburl + "/+blobs?field=blobfile", expect_errors=True)

    assert r.status_code == 404

    # unocide textfile upload test

    r = c.post_json("/blob_objects", {})

    bloburl = r.json["links"][0]["href"]

    r = c.get(bloburl)

    testimg = os.path.join(os.path.dirname(__file__), "testtxt.txt")

    r = c.post(bloburl + "/+blobs?field=blobfile", upload_files=[("upload", testimg)])

    assert r.status_code == 200

    r = c.get(bloburl)

    assert r.json["data"]["blobs"]["blobfile"]

    r = c.get(bloburl + "/+blobs?field=blobfile")

    with open(testimg, "rb") as ti:
        assert r.body == ti.read()

    assert r.headers.get("Content-Type") == "text/plain; charset=UTF-8"

    if os.path.exists(FSBLOB_DIR):
        shutil.rmtree(FSBLOB_DIR)
