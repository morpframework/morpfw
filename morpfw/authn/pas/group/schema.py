import typing
from dataclasses import dataclass, field

from morpfw.crud.schema import Schema

from ....validator.field import valid_identifier
from ..app import App


def valid_group_identifier(request, schema, field, value, mode=None):
    if value == "__default__":
        return
    return valid_identifier(request, schema, field, value, mode)


@dataclass
class GroupSchema(Schema):
    parent: typing.Optional[str] = field(
        default=None, metadata={"editable": False, "required": False}
    )
    groupname: typing.Optional[str] = field(
        default=None,
        metadata={
            "editable": False,
            "required": True,
            "validators": [valid_group_identifier],
        },
    )

    __unique_constraint__ = ["groupname", "deleted"]


@dataclass
class MemberSchema(Schema):
    users: typing.List[str] = field(default_factory=list, metadata={"required": True})
