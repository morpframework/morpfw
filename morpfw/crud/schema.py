import jsonobject
from uuid import uuid4
from ..interfaces import ISchema
from .app import App
from dataclasses import dataclass, field
from datetime import datetime
import typing


@dataclass
class Schema(ISchema):

    id: typing.Optional[int] = None
    uuid: typing.Optional[str] = field(default_factory=lambda: uuid4().hex)
    creator: typing.Optional[str] = None
    created: typing.Optional[datetime] = None
    modified: typing.Optional[datetime] = None
    state: typing.Optional[str] = None
    deleted: typing.Optional[datetime] = None
    blobs: typing.Optional[dict] = field(
        default_factory=dict, metadata={'morpfw': {
            'exclude_if_empty': True
        }})
    xattrs: typing.Optional[dict] = field(
        default_factory=dict, metadata={'morpfw': {
            'exclude_if_empty': True
        }})


@App.identifierfields(schema=Schema)
def identifierfields(schema):
    return ['uuid']


@App.default_identifier(schema=Schema)
def default_identifier(schema, obj, request):
    fields = request.app.get_identifierfields(schema)
    res = []
    for f in fields:
        if f == 'uuid':
            res.append(uuid4().hex)
        else:
            res.append(obj[f])
    return res
