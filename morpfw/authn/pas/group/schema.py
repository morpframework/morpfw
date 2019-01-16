from morpfw import Schema
from ..app import App
from dataclasses import dataclass, field
import typing


@dataclass
class GroupSchema(Schema):
    groupname: typing.Optional[str] = field(default=None, metadata={
        'morpfw': {'required': True}})


@App.identifierfields(schema=GroupSchema)
def group_identifierfields(schema):
    return ['groupname']


@dataclass
class MemberSchema(Schema):
    users: typing.List[str] = field(default_factory=list, metadata={
                                    'morpfw': {'required': True}})
