import typing
from dataclasses import dataclass, field
from datetime import datetime
from pprint import pprint
from uuid import uuid4

import pytz

import colander
from inverter import dc2colander, dc2colanderjson

from ..interfaces import ISchema
from .app import App
from .errors import FieldValidationError, FormValidationError, ValidationError
from .relationship import BackReference, Reference


@dataclass
class BaseSchema(ISchema):
    @classmethod
    def validate(
        cls, request, data, deserialize=True, json=True, update_mode=False, **kwargs
    ):
        params = {}

        if not update_mode:
            if json:
                cschema = dc2colanderjson.convert(cls, request=request)
            else:
                cschema = dc2colander.convert(
                    cls, request=request, default_tzinfo=request.timezone()
                )

        else:
            if json:
                cschema = dc2colanderjson.convert(
                    cls, request=request, include_fields=data.keys(), mode="update",
                )
            else:
                cschema = dc2colander.convert(
                    cls,
                    request=request,
                    include_fields=data.keys(),
                    mode="update",
                    default_tzinfo=request.timezone(),
                )
        cs = cschema()
        # FIXME: need to pass context here
        cs = cs.bind(request=request, **kwargs)
        if not deserialize:
            # FIXME: can we skip this and immediately validate?

            data = cs.serialize(data)

        try:
            data = cs.deserialize(data)
        except colander.Invalid as e:
            errors = e.asdict()
            params["field_errors"] = [
                FieldValidationError(path=k, message=m) for k, m in errors.items()
            ]
        if params:
            raise ValidationError(**params)

        return data


@dataclass
class Schema(BaseSchema):

    id: typing.Optional[int] = field(
        default=None, metadata={"primary_key": True, "autoincrement": True}
    )
    uuid: typing.Optional[str] = field(
        default_factory=lambda: uuid4().hex,
        metadata={"format": "uuid", "index": True, "unique": True},
    )
    creator: typing.Optional[str] = field(
        default=None, metadata={"format": "uuid", "index": True, "length": 256}
    )
    created: typing.Optional[datetime] = field(
        default_factory=lambda: datetime.now(tz=pytz.UTC), metadata={"index": True}
    )
    modified: typing.Optional[datetime] = field(
        default_factory=lambda: datetime.now(tz=pytz.UTC), metadata={"index": True}
    )
    state: typing.Optional[str] = field(
        default=None, metadata={"index": True, "length": 64}
    )
    deleted: typing.Optional[datetime] = field(default=None, metadata={"index": True})

    blobs: typing.Optional[dict] = field(
        default_factory=dict, metadata={"exclude_if_empty": True}
    )
    xattrs: typing.Optional[dict] = field(
        default_factory=dict, metadata={"exclude_if_empty": True}
    )

    __unique_constraint__ = []  # type: ignore
    __references__ = []  # type: ignore
    __backreferences__ = []  # type: ignore
    __validators__ = []  # type: ignore
    __protected_fields__ = [
        "id",
        "blobs",
        "state",
        "xattrs",
        "modified",
        "created",
        "uuid",
        "creator",
        "deleted",
    ]


@App.identifierfield(schema=Schema)
def identifierfield(schema):
    return "uuid"


@App.default_identifier(schema=Schema)
def default_identifier(schema, obj, request):
    idfield = request.app.get_identifierfield(schema)
    if idfield == "uuid":
        obj[idfield] = uuid4().hex
    return obj[idfield]
