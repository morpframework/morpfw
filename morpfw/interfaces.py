import abc
from typing import Any, BinaryIO, List, Optional, Sequence, Type, Union

import morepath
import webob

_marker = object()


class ISchema(object):
    """
    Schema represent the fields available in a content type. MorpFW uses
    python dataclass as its schema we provide transformation function to
    transform dataclass into other schema format (eg: JSL, colander, etc)
    """


class IDataProvider(abc.ABC):
    """
    Data provider wraps around backend storage model object
    (eg: SQLAlchemy model object) and provide a bridge for getting and setting
    data from model.
    """

    @abc.abstractmethod
    def __init__(self, schema: Type[ISchema], data: dict, storage: "IStorageBase"):
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
    def setdefault(self, key, value):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, key, default=None):
        raise NotImplementedError

    @abc.abstractmethod
    def set(self, key, value):
        raise NotImplementedError

    @abc.abstractmethod
    def items(self):
        raise NotImplementedError

    @abc.abstractmethod
    def keys(self):
        raise NotImplementedError

    @abc.abstractmethod
    def as_dict(self):
        """Returns dictionary representation of the data, where python objects
        such as ``datetime`` remains as python objects"""
        raise NotImplementedError

    @abc.abstractmethod
    def as_json(self):
        """Returns JSON-safe dictionary representation of the data. Any python
        objects are serialized into JSON-safe data type"""
        raise NotImplementedError

    def _is_json_type(self, value):
        """Check if a value is JSON-safe"""
        if value is None:
            return True
        return (
            isinstance(value, str)
            or isinstance(value, list)
            or isinstance(value, dict)
            or isinstance(value, float)
            or isinstance(value, int)
        )


class IBlob(abc.ABC):
    @abc.abstractmethod
    def __init__(
        self,
        uuid,
        filename: str,
        mimetype: Optional[str] = None,
        size: Optional[int] = None,
        encoding: Optional[str] = None,
    ):
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
    def put(
        self,
        field: str,
        fileobj: BinaryIO,
        filename: str,
        mimetype: Optional[str] = None,
        size: Optional[int] = None,
        encoding: Optional[str] = None,
        uuid: Optional[str] = None,
    ) -> IBlob:
        """Receive and store blob data"""
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, uuid: str) -> Optional[IBlob]:
        """Return blob data"""
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, uuid: str):
        """Delete blob data"""
        raise NotImplementedError


class IStorageBase(abc.ABC):
    """Basic storage backend"""

    @abc.abstractmethod
    def __init__(
        self, request: morepath.Request, blobstorage: Optional[IBlobStorage] = None
    ):
        super().__init__()

    @abc.abstractmethod
    def create(self, data: dict) -> "IModel":
        """Create a model from submitted data"""
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, identifier) -> Optional["IModel"]:
        """return model from identifier"""
        raise NotImplementedError

    @abc.abstractmethod
    def search(
        self,
        query: Optional[dict] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        order_by: Union[None, list, tuple] = None,
    ) -> Sequence["IModel"]:
        """return search result based on specified rulez query"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_by_id(self, id) -> Optional["IModel"]:
        """return model from internal ID"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_by_uuid(self, uuid) -> Optional["IModel"]:
        """return model from uuid"""
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
    """Aggregateable storage"""

    @abc.abstractmethod
    def aggregate(
        self,
        query: Optional[dict] = None,
        group: Optional[dict] = None,
        order_by: Union[None, list, tuple] = None,
    ) -> list:
        """return aggregation result based on specified rulez query and group"""
        raise NotImplementedError


class IModel(abc.ABC):
    """
    Model is a representation of a data object. It
    provide a common set of API which is then delegated down
    to the storage provider.

    Model is subscriptable and you can use it like a dictionary
    to access stored data.

    :param request: the request object
    :param storage: storage provider
    :param data: initial data on this model

    """

    #: Set whether object is linkable or not.
    #: If an object is linkable, its json result
    #: will have links attribute
    linkable: bool

    @abc.abstractproperty
    def schema(self) -> Type[ISchema]:
        """The dataclass schema which this model will be using"""
        raise NotImplementedError

    #: When set to True, will enable PATCH view to update model
    update_view_enabled: bool

    #: When set to True, will enable DELETE view to delete model
    delete_view_enabled: bool

    #: Field name on the model data which will be storing blob references
    blobstorage_field: str

    #: List of blob field names allowed on this model
    blob_fields: List[str]

    #: url identifier for this model
    identifier: str

    #: uuid of this model
    uuid: str

    #: Data provider
    data: IDataProvider

    #: List of fields that should be hidden from output
    hidden_fields: list

    @abc.abstractmethod
    def __init__(
        self, request: morepath.Request, collection: "ICollection", data: dict,
    ):
        super().__init__()

    @abc.abstractmethod
    def __getitem__(self, key):
        raise NotImplementedError

    @abc.abstractmethod
    def update(self, newdata: dict, secure: bool):
        """Update model with new data"""
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self):
        """Delete model"""
        raise NotImplementedError

    @abc.abstractmethod
    def save(self):
        """Persist model data into backend storage"""
        raise NotImplementedError

    @abc.abstractmethod
    def json(self) -> dict:
        """Convert model to JSON-safe dictionary"""
        raise NotImplementedError

    @abc.abstractmethod
    def links(self) -> list:
        """Generate links for this model"""
        raise NotImplementedError

    @abc.abstractmethod
    def rulesprovider(self):
        """Return pluggable business rule adapter for this model"""
        raise NotImplementedError

    @abc.abstractmethod
    def statemachine(self):
        """Return PyTransition statemachine adapter for this model"""
        raise NotImplementedError

    @abc.abstractmethod
    def xattrprovider(self):
        """Return extended attributes provider for this model"""
        raise NotImplementedError

    @abc.abstractmethod
    def set_initial_state(self):
        """Initialize default statemachine state for this model"""
        raise NotImplementedError

    @abc.abstractmethod
    def put_blob(
        self,
        field: str,
        fileobj: BinaryIO,
        filename: str,
        mimetype: Optional[str] = None,
        size: Optional[int] = None,
        encoding: Optional[str] = None,
    ) -> IBlob:
        """Receive and store blob object"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_blob(self, field: str) -> IBlob:
        """Return blob"""
        raise NotImplementedError

    @abc.abstractmethod
    def delete_blob(self, field: str):
        """Delete blob"""
        raise NotImplementedError

    # event hooks

    def after_created(self) -> None:
        """Triggered after resource have been created"""

    def before_update(self, newdata: dict) -> None:
        """Triggered before updating resource with new values"""

    def after_updated(self) -> None:
        """Triggered after resource have been created"""

    def before_delete(self) -> bool:
        """
        Triggered before deleting resource
        
        If the return value is False-ish, delete will be prevented
        """
        return True

    def before_blobput(
        self,
        field: str,
        fileobj: BinaryIO,
        filename: str,
        mimetype: Optional[str] = None,
        size: Optional[int] = None,
        encoding: Optional[str] = None,
    ) -> None:
        """Triggered before BLOB is stored"""

    def after_blobput(self, field: str, blob: IBlob) -> None:
        """Triggered after BLOB is stored"""

    def before_blobdelete(self, field: str) -> None:
        """
        Triggered before BLOB is deleted
        
        If the return value is False-ish, delete will be prevented
        """
        return True


class ICollection(abc.ABC):
    """Collection provide an API for querying group of model from its storage"""

    @abc.abstractmethod
    def search(
        self,
        query: Optional[dict] = None,
        offset: int = 0,
        limit: Optional[int] = None,
        order_by: Optional[tuple] = None,
        secure: bool = False,
    ) -> List[IModel]:
        """Search for models

        Filtering is done through ``rulez`` based JSON/dict query, which
        defines boolean statements in JSON/dict structure.

        : param query: Rulez based query
        : param offset: Result offset
        : param limit: Maximum number of result
        : param order_by: Tuple of ``(field, order)`` where ``order`` is
                         ``'asc'`` or ``'desc'``
        : param secure: When set to True, this will filter out any object which
                       current logged in user is not allowed to see

        : todo: ``order_by`` need to allow multiple field ordering
        """
        raise NotImplementedError

    @abc.abstractmethod
    def aggregate(
        self,
        query: Optional[dict] = None,
        group: Optional[dict] = None,
        order_by: Optional[tuple] = None,
    ) -> List[IModel]:
        """Get aggregated results

        : param query: Rulez based query
        : param group: Grouping structure
        : param order_by: Tuple of ``(field, order)`` where ``order`` is
                         ``'asc'`` or ``'desc'``

        : todo: Grouping structure need to be documented

        """
        raise NotImplementedError

    @abc.abstractmethod
    def create(self, data: dict) -> IModel:
        """Create a model from data"""
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, identifier) -> IModel:
        """Get model by url identifier key"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_by_uuid(self, uuid: str) -> IModel:
        """Get model by uuid"""
        raise NotImplementedError

    @abc.abstractmethod
    def json(self) -> dict:
        """JSON-safe dictionary representing this collection"""
        raise NotImplementedError

    @abc.abstractmethod
    def links(self) -> list:
        """Links related to this collection"""
        raise NotImplementedError

    def before_create(self, data: dict) -> None:
        """Triggered before the creation of resource"""


class IStateMachine(abc.ABC):
    @abc.abstractproperty
    def states(self) -> List:
        """List of ``pytransitions`` states"""
        raise NotImplementedError

    @abc.abstractproperty
    def readonly_states(self) -> List:
        """List of readonly states"""
        raise NotImplementedError

    @abc.abstractproperty
    def transitions(self) -> List:
        """List of ``pytransitions`` transitions"""
        raise NotImplementedError

    @abc.abstractmethod
    def _get_state(self) -> Optional[str]:
        """Get current state"""
        raise NotImplementedError

    @abc.abstractmethod
    def _set_state(self, val):
        """Set current state"""
        raise NotImplementedError

    state = property(_get_state, _set_state, doc="Current resource state")

    @abc.abstractmethod
    def get_triggers(self) -> List:
        """Returns list of available triggers"""
        raise NotImplementedError


class IXattrProvider(abc.ABC):
    @abc.abstractproperty
    def schema(self) -> Type[Any]:
        """Schema to use for data validation"""
        raise NotImplementedError

    # Set to True to allow arbitrary properties besides
    # the properties defined on the schema
    additional_properties: bool = False

    @abc.abstractmethod
    def jsonschema(self) -> dict:
        """Returns JSON Schema for Xattr"""
        raise NotImplementedError

    @abc.abstractmethod
    def as_dict(self):
        """Returns dictionary representation of the data, where python objects
        such as ``datetime`` remains as python objects"""
        raise NotImplementedError

    @abc.abstractmethod
    def as_json(self):
        """Returns JSON-safe dictionary representation of the data. Any python
        objects are serialized into JSON-safe data type"""
        raise NotImplementedError

    @abc.abstractmethod
    def process_update(self, newdata: dict):
        """Validate received data and then update the extended attributes"""
        raise NotImplementedError

    @abc.abstractmethod
    def update(self, newdata: dict):
        """Update extended attributes"""
        raise NotImplementedError

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
    def get(self, key, default=_marker):
        raise NotImplementedError


class ISearchProvider(abc.ABC):
    @abc.abstractmethod
    def parse_query(self, qs: str) -> dict:
        """Parse query string from search query and convert it into rulez query
        dictionary. The dictionary would be passed to search method afterwards,
        which you can then parse into your backend search query.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def search(
        self,
        query: Optional[dict] = None,
        offset: int = 0,
        limit: Optional[int] = None,
        order_by: Union[None, list, tuple] = None,
    ) -> List[IModel]:
        """Execute search and return list of model objects"""
        raise NotImplementedError


class IAggregateProvider(abc.ABC):
    @abc.abstractmethod
    def parse_query(self, qs: str) -> dict:
        """Parse query string from search query and convert it into rulez query
        dictionary. The dictionary would be passed to aggregate method afterwards,
        which you can then parse into your backend search query.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def parse_group(self, qs: str) -> dict:
        """Parse query string from group query and convert it into dictionary
        representation. The dictionary would be passed to aggregate method afterwards,
        which you can then parse into your backend aggregate query.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def aggregate(
        self,
        query: Optional[dict] = None,
        group: Optional[dict] = None,
        order_by: Union[None, list, tuple] = None,
    ) -> list:
        """return aggregation result based on specified rulez query and group"""
        raise NotImplementedError
