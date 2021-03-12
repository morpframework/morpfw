import datetime
import hashlib
import json
import os
import typing
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import morepath
import morpfw

from ..app import App
from .base import Blob, BlobStorage

# 1MB
WRITE_BUFF_SIZE = 1073741824


class FSBlob(Blob):
    def __init__(self, path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = path

    def open(self):
        return open(self.path, "rb")

    def get_size(self):
        stat = os.stat(self.path)
        return stat.st_size


class FSBlobStorage(BlobStorage):
    def __init__(self, request: morepath.Request, path: str):
        self.path = path
        self.request = request

    def _uuid_path(self, uuid):
        first = uuid[:2]
        second = uuid[2:4]
        return os.path.join(self.path, first, second)

    def _meta_path(self, obj_path):
        return "%s.metadata.json" % obj_path

    def put(
        self,
        fileobj: typing.BinaryIO,
        filename: str,
        mimetype: typing.Optional[str] = None,
        size: typing.Optional[int] = None,
        encoding: typing.Optional[str] = None,
        uuid: typing.Optional[str] = None,
    ) -> FSBlob:

        if uuid is None:
            uuid = uuid4().hex

        obj_path = os.path.join(self._uuid_path(uuid), uuid)
        meta_path = self._meta_path(obj_path)
        Path(self._uuid_path(uuid)).mkdir(parents=True, exist_ok=True)

        fileobj.seek(0)
        hash = hashlib.sha256()
        with open(obj_path, "wb") as o:
            while True:
                data = fileobj.read(WRITE_BUFF_SIZE)
                if not data:
                    break
                hash.update(data)
                o.write(data)

        meta = {
            "uuid": uuid,
            "filename": filename,
            "mimetype": mimetype,
            "size": size,
            "encoding": encoding,
            "sha256sum": hash.hexdigest()
        }
        with open(meta_path, "w") as mo:
            mo.write(json.dumps(meta))

        meta["path"] = obj_path
        return FSBlob(**meta)

    def get(self, uuid: str) -> typing.Optional[Blob]:
        obj_path = os.path.join(self._uuid_path(uuid), uuid)
        meta_path = self._meta_path(obj_path)

        if not os.path.exists(meta_path):
            return None

        meta: dict = {}
        with open(meta_path) as mo:
            meta = json.loads(mo.read())

        meta["path"] = obj_path
        return FSBlob(**meta)

    def delete(self, uuid: str):
        obj_path = os.path.join(self._uuid_path(uuid), uuid)
        meta_path = self._meta_path(obj_path)

        if os.path.exists(obj_path):
            os.unlink(obj_path)

        if os.path.exists(meta_path):
            os.unlink(meta_path)


@App.blobstorage_factory("fsblob")
def get_fsblobstorage(request, uri):
    parsed = urlparse(uri)
    home_env = request.app.home_env
    if home_env not in os.environ:
        if 'MORP_WORKDIR' in os.environ:
            warnings.warn("MORP_WORKDIR environment is deprecated, use %s" %
                        home_env, DeprecationWarning)
            home_env = 'MORP_WORKDIR'

    if parsed.netloc == "":
        path = parsed.path
    else:
        path = os.path.join(
            os.environ.get(home_env, os.getcwd()),
            parsed.netloc,
            *parsed.path.split("/")
        )
    return FSBlobStorage(request, path)
