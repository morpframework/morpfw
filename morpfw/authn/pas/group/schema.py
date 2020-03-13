import typing
from dataclasses import dataclass, field

from morpfw.crud.schema import Schema

from ..app import App


@dataclass
class GroupSchema(Schema):
    parent: typing.Optional[str] = None
    groupname: typing.Optional[str] = field(default=None, metadata={"required": True})


@App.identifierfield(schema=GroupSchema)
def group_identifierfield(schema):
    return "groupname"


@dataclass
class MemberSchema(Schema):
    users: typing.List[str] = field(default_factory=list, metadata={"required": True})
