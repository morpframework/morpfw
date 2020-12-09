import os
import typing

from webob import exc
from webob.dec import wsgify
from webob.response import Response
from webob.static import FileIter

from ...interfaces import IBlob, IBlobStorage

BLOCK_SIZE = 1 << 16


class Blob(IBlob):
    def __init__(
        self, uuid, filename, mimetype=None, size=None, encoding=None, sha256sum=None
    ):
        self.uuid = uuid
        if size and size < 0:
            size = None
        self.size = size
        self.filename = filename
        self.mimetype = mimetype
        self.encoding = encoding
        self.sha256sum = sha256sum
        super().__init__(uuid, filename, mimetype, size, encoding)

    def get_size(self) -> int:
        return self.size

    @wsgify
    def __call__(self, req):
        if req.method not in ("GET", "HEAD"):
            return exc.HTTPMethodNotAllowed("You cannot %s a file" % req.method)

        disposition = req.GET.get("disposition", "attachment")
        try:
            file = self.open()
        except (IOError, OSError) as e:
            msg = "You are not permitted to view this file (%s)" % e
            return exc.HTTPForbidden(msg)

        if "wsgi.file_wrapper" in req.environ:
            app_iter = req.environ["wsgi.file_wrapper"](file, BLOCK_SIZE)
        else:
            app_iter = FileIter(file)

        return Response(
            app_iter=app_iter,
            content_length=self.get_size(),
            content_type=self.mimetype,
            content_encoding=self.encoding,
            content_disposition='%s; filename="%s"' % (disposition, self.filename),
            # @@ etag
        ).conditional_response_app


class BlobStorage(IBlobStorage):
    pass


class NullBlobStorage(BlobStorage):
    def put(
        self,
        fileobj: typing.BinaryIO,
        filename: str,
        mimetype: typing.Optional[str] = None,
        size: typing.Optional[int] = None,
        encoding: typing.Optional[str] = None,
        uuid: typing.Optional[str] = None,
    ) -> Blob:
        raise NotImplementedError

    def get(self, uuid: str) -> typing.Optional[Blob]:
        raise NotImplementedError

    def delete(self, uuid: str):
        raise NotImplementedError
