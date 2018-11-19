from .storage import Group, Membership, RoleAssignment
from ..model import NAME_PATTERN
from morpfw.crud import Collection, Model, Schema
from ..app import App
import jsl
from morpfw.crud import errors as cruderrors
from .. import exc
import jsonobject
from .schema import GroupSchema, MemberSchema
from ..exc import GroupExistsError


class GroupCollection(Collection):
    schema = GroupSchema
    exist_exc = GroupExistsError


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
