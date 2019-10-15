import copy
from ..blobstorage.base import NullBlobStorage
from ..errors import BlobStorageNotImplementedError
from ...interfaces import IStorage


class BaseStorage(IStorage):

    use_transactions = True

    blobstorage = None

    @property
    def model(self):
        raise NotImplementedError

    def __init__(self, request, blobstorage=None):
        self.request = request
        self.app = request.app
        self.blobstorage = blobstorage
        super().__init__(request, blobstorage)

    def set_identifier(self, obj, identifier):
        idfield = self.app.get_identifierfield(self.model.schema)
        obj[idfield] = identifier

    def set_schema_defaults(self, data):
        obj = self.model.schema(**data)
        return obj.__dict__

#	def create(self, data):
#		raise NotImplementedError
#
#	def search(self, query=None, limit=None):
#		raise NotImplementedError
#
#	def aggregate(self, query=None, group=None, order_by=None):
#		raise NotImplementedError
#
#	def get(self, identifier):
#		raise NotImplementedError
#
#	def get_by_id(self, id):
#		raise NotImplementedError
#
#	def get_by_uuid(self, uuid):
#		raise NotImplementedError
#
#	def update(self, identifier, data):
#		raise NotImplementedError
#
#	def delete(self, identifier, model):
#		raise NotImplementedError

    def _blob_guard(self):
        if self.blobstorage is None or isinstance(self.blobstorage, NullBlobStorage):
            raise BlobStorageNotImplementedError(
                'Storage does not implement blobstorage')

    def get_blob(self, uuid):
        self._blob_guard()
        return self.blobstorage.get(uuid)

    def put_blob(self, fileobj, filename, mimetype=None, size=None, encoding=None):
        self._blob_guard()
        blob = self.blobstorage.put(
            fileobj, filename, mimetype, size, encoding)
        return blob

    def delete_blob(self, uuid):
        self._blob_guard()
        self.blobstorage.delete(uuid)
