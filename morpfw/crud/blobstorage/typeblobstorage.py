import datetime
import json
import os
import typing
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import deform
import morepath
import morpfw
import morpfw.sql
import sqlalchemy as sa

from ..app import App
from .base import Blob, BlobStorage


@dataclass
class TypeBlobStoreSchema(morpfw.Schema):

    file: typing.Optional[deform.FileData] = None


class TypeBlobStoreMixin(object):

    filename = sa.Column(sa.String(1024))
    mimetype = sa.Column(sa.String(256))
    size = sa.Column(sa.Integer())
    encoding = sa.Column(sa.String(128))
    fp = sa.Column(sa.LargeBinary())


class TypeBlobStoreCollection(morpfw.Collection):
    schema = TypeBlobStoreSchema

    def _create(self, data):
        data = data["file"]
        data["fp"] = data["fp"].read()
        return super()._create(data)


class TypeBlobStoreModel(morpfw.Model):
    schema = TypeBlobStoreSchema

    def __setitem__(self, key, value):
        if key == "file":
            self.data["filename"] = value["filename"]
            self.data["mimetype"] = value["mimetype"]
            self.data["encoding"] = value["encoding"]
            self.data["size"] = value["size"]
            if hasattr(value["fp"], "read"):
                self.data["fp"] = value["fp"].read()
            else:
                self.data["fp"] = value["fp"]
            return
        self.data[key] = value

    def __getitem__(self, key):
        if key == "file":
            return {
                "filename": self.data["filename"],
                "mimetype": self.data["mimetype"],
                "encoding": self.data["encoding"],
                "size": self.data["size"],
                "uid": self.uuid,
                "fp": BytesIO(self.data["fp"]),
            }
        return self.data[key]

    def __delitem__(self, key):
        if key == "file":
            del self.data["filename"]
            del self.data["mimetype"]
            del self.data["encoding"]
            del self.data["size"]
            del self.data["fp"]
        del self.data[key]

    def __dict__(self):
        res = self.data.as_dict()
        res["file"] = {
            "filename": res["filename"],
            "mimetype": res["mimetype"],
            "encoding": res["encoding"],
            "size": res["size"],
            "uid": self.uuid,
            "fp": BytesIO(res["fp"]),
        }
        for k in ["filename", "mimetype", "encoding", "size", "fp"]:
            del res[k]
        return res



class TypeBlob(Blob):
    def __init__(self, obj, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.obj = obj

    def open(self):
        return BytesIO(self.obj["fp"])

    def get_size(self):
        return self.obj["size"]


class TypeBlobStorage(BlobStorage):
    """ Store blob in a resource type """

    def __init__(self, request: morepath.Request, type_name: str):
        self.type_name = type_name
        self.request = request

    def put(
        self,
        fileobj: typing.BinaryIO,
        filename: str,
        mimetype: typing.Optional[str] = None,
        size: typing.Optional[int] = None,
        encoding: typing.Optional[str] = None,
        uuid: typing.Optional[str] = None,
    ) -> TypeBlob:
        data = {
            "file": {
                "uid": uuid4().hex,
                "filename": filename,
                "mimetype": mimetype,
                "size": size,
                "encoding": encoding,
                "fp": fileobj,
            }
        }
        col = self.request.get_collection(self.type_name)
        if uuid is not None:
            obj = col.get(uuid)
            obj.update(data, deserialize=False)
        else:
            obj = col.create(data, deserialize=False)

        meta = {
            "uuid": obj.uuid,
            "filename": filename,
            "mimetype": mimetype,
            "size": size,
            "encoding": encoding,
        }
        return TypeBlob(obj, **meta)

    def get(self, uuid: str) -> typing.Optional[TypeBlob]:
        col = self.request.get_collection(self.type_name)
        obj = col.get(uuid)
        if not obj:
            return None

        meta = {
            "uuid": obj.uuid,
            "filename": obj["filename"],
            "mimetype": obj["mimetype"],
            "size": obj["size"],
            "encoding": obj["encoding"],
        }
        return TypeBlob(obj, **meta)

    def delete(self, uuid: str):
        col = self.request.get_collection(self.type_name)
        obj = col.get(uuid)
        if obj:
            obj.delete()
