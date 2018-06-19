from ..dbmodel import Group, Membership, RoleAssignment
from .base import BaseSchema, NAME_PATTERN
from ...jslcrud import Collection, Model
from ..app import App
import jsl
from ...jslcrud import errors as cruderrors
from .. import exc


class GroupSchema(BaseSchema):
    class Options(object):
        title = 'group'
        additional_properties = True
    groupname = jsl.StringField(required=True, pattern=NAME_PATTERN)
    members = jsl.ArrayField(items=jsl.StringField(), required=False)
    attrs = jsl.DictField(required=False)
    created = jsl.StringField(required=False)
    modified = jsl.StringField(required=False)


@App.jslcrud_identifierfields(schema=GroupSchema)
def group_identifierfields(schema):
    return ['groupname']


class MemberSchema(BaseSchema):
    users = jsl.ArrayField(items=jsl.StringField(), required=True)


class GroupCollection(Collection):
    schema = GroupSchema

    def _create(self, data):
        exists = self.storage.get(data['groupname'])
        if exists:
            raise exc.GroupExistsError(data['groupname'])
        return super(GroupCollection, self)._create(data)


class GroupModel(Model):
    schema = GroupSchema

    def members(self):
        members = self.storage.get_members(self.identifier)
        active_members = [
            member for member in members if member.data.get('state') == 'active']
        return active_members

    def add_members(self, usernames):
        self.storage.add_group_members(self.identifier, usernames)

    def remove_members(self, usernames):
        self.storage.remove_group_members(self.identifier, usernames)

    def get_member_roles(self, username):
        return self.storage.get_group_user_roles(self.identifier, username)

    def grant_member_role(self, username, rolename):
        if username not in [m.identifier for m in self.members()]:
            self.add_members([username])
        self.storage.grant_group_user_role(self.identifier, username, rolename)

    def revoke_member_role(self, username, rolename):
        self.storage.revoke_group_user_role(
            self.identifier, username, rolename)
        if (not self.get_member_roles(username) and
                self.identifier != '__default__'):
            self.remove_members([username])
