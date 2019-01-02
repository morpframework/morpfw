import abc
import morepath
import webob
from typing import Optional, Union, BinaryIO, List, Sequence, Type
import jsonobject


class ISchema(jsonobject.JsonObject):
    pass


class IBlob(abc.ABC):

    @abc.abstractmethod
    def __init__(self, uuid, filename: str,
                 mimetype: Optional[str] = None,
                 size: Optional[int] = None,
                 encoding: Optional[str] = None):
        super().__init__()

    @abc.abstractmethod
    def open(self) -> BinaryIO:
        raise NotImplementedError

    @abc.abstractmethod
    def get_size(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def __call__(self, req: webob.Request) -> webob.Response:
        raise NotImplementedError


class IBlobStorage(abc.ABC):

    @abc.abstractmethod
    def put(self, field: str, fileobj: BinaryIO,
            filename: str,
            mimetype: Optional[str] = None,
            size: Optional[int] = None,
            encoding: Optional[str] = None,
            uuid: Optional[str] = None) -> IBlob:
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, uuid: str) -> Optional[IBlob]:
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, uuid: str):
        raise NotImplementedError


class IStorageBase(abc.ABC):
    @abc.abstractmethod
    def __init__(self, request: morepath.Request,
                 blobstorage: Optional[IBlobStorage] = None):
        super().__init__()

    @abc.abstractmethod
    def create(self, data: dict) -> 'IModel':
        """Create a model from submitted data"""
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, identifier) -> Optional['IModel']:
        """return model from identifier"""
        raise NotImplementedError

    @abc.abstractmethod
    def search(self, query: Optional[dict] = None, offset: Optional[int] = None,
               limit: Optional[int] = None,
               order_by: Union[None, list, tuple] = None) -> Sequence['IModel']:
        """return search result based on specified rulez query"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_by_id(self, id) -> Optional['IModel']:
        """return model from internal ID"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_by_uuid(self, uuid) -> Optional['IModel']:
        """return model from GUID"""
        raise NotImplementedError

    @abc.abstractmethod
    def update(self, identifier, data):
        """update model with values from data"""
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, identifier, model):
        """delete model data"""
        raise NotImplementedError


class IStorage(IStorageBase):
    @abc.abstractmethod
    def aggregate(self, query: Optional[dict] = None,
                  group: Optional[dict] = None,
                  order_by: Union[None, list, tuple] = None) -> list:
        """return aggregation result based on specified rulez query and group"""
        raise NotImplementedError


class IModel(abc.ABC):

    linkable: bool
    schema: Type[ISchema]
    update_view_enabled: bool
    delete_view_enabled: bool
    statemachine_view_enabled: bool
    blobstorage_field: str
    blob_fields: List[str]
    identifier: str
    uuid: str

    @abc.abstractmethod
    def __init__(self, request: morepath.Request,
                 storage: IStorage, data: dict):
        super().__init__()

    @abc.abstractmethod
    def __setitem__(self, key, value):
        raise NotImplementedError

    @abc.abstractmethod
    def __getitem__(self, key):
        raise NotImplementedError

    @abc.abstractmethod
    def __delitem__(self, key):
        raise NotImplementedError

    @abc.abstractmethod
    def update(self, newdata: dict):
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self):
        raise NotImplementedError

    @abc.abstractmethod
    def save(self):
        raise NotImplementedError

    @abc.abstractmethod
    def json(self) -> dict:
        raise NotImplementedError

    @abc.abstractmethod
    def links(self) -> list:
        raise NotImplementedError

    @abc.abstractmethod
    def rules_adapter(self):
        raise NotImplementedError

    @abc.abstractmethod
    def statemachine(self):
        raise NotImplementedError

    @abc.abstractmethod
    def set_initial_state(self):
        raise NotImplementedError

    @abc.abstractmethod
    def put_blob(self, field: str, fileobj: BinaryIO,
                 filename: str,
                 mimetype: Optional[str] = None,
                 size: Optional[int] = None,
                 encoding: Optional[str] = None) -> IBlob:
        raise NotImplementedError

    @abc.abstractmethod
    def get_blob(self, field: str) -> IBlob:
        raise NotImplementedError

    @abc.abstractmethod
    def delete_blob(self, field: str):
        raise NotImplementedError
