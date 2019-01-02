import jsonobject
from morpfw import Schema
from ..app import App


class GroupSchema(Schema):
    groupname = jsonobject.StringProperty(
        required=True)  # , pattern=NAME_PATTERN)


@App.identifierfields(schema=GroupSchema)
def group_identifierfields(schema):
    return ['groupname']


class MemberSchema(Schema):
    users = jsonobject.ListProperty(str, required=True)
