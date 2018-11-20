import jsonobject
from morpfw import Schema
from ..app import App


class GroupSchema(Schema):
    groupname = jsonobject.StringProperty(
        required=True)  # , pattern=NAME_PATTERN)
    members = jsonobject.ListProperty(str, required=False)
    attrs = jsonobject.DictProperty(required=False)
    created = jsonobject.StringProperty(required=False)
    modified = jsonobject.StringProperty(required=False)


@App.identifierfields(schema=GroupSchema)
def group_identifierfields(schema):
    return ['groupname']


class MemberSchema(Schema):
    users = jsonobject.ListProperty(str, required=True)
