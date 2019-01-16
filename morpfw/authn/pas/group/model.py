from ..model import NAME_PATTERN
from morpfw.crud import Collection, Model, Schema
from ..app import App
import jsl
from morpfw.crud import errors as cruderrors
from .. import exc
from .schema import GroupSchema, MemberSchema
from ..exc import GroupExistsError


class GroupCollection(Collection):
    schema = GroupSchema
    exist_exc = GroupExistsError


class GroupModel(Model):
    schema = GroupSchema

    def get_user_by_userid(self, userid):
        return self.storage.get_user_by_userid(userid)

    def get_user_by_username(self, username):
        return self.storage.get_user_by_username(username)

    def members(self):
        members = self.storage.get_members(self.identifier)
        active_members = [
            member for member in members if member.data.get('state') == 'active']
        return active_members

    def add_members(self, userids):
        self.storage.add_group_members(self.identifier, userids)

    def remove_members(self, userids):
        self.storage.remove_group_members(self.identifier, userids)

    def get_member_roles(self, userid):
        return self.storage.get_group_user_roles(self.identifier, userid)

    def grant_member_role(self, userid, rolename):
        if userid not in [m.userid for m in self.members()]:
            self.add_members([userid])
        self.storage.grant_group_user_role(self.identifier, userid, rolename)

    def revoke_member_role(self, userid, rolename):
        self.storage.revoke_group_user_role(
            self.identifier, userid, rolename)
        if (not self.get_member_roles(userid) and
                self.identifier != '__default__'):
            self.remove_members([userid])

    def _links(self):
        links = []
        for m in self.members():
            links.append({
                'rel': 'member',
                'href': self.request.link(m)
            })
        return links
