import rulez
from morpfw.crud import Collection, Model, Schema
from morpfw.crud import errors as cruderrors

from .. import exc
from ..app import App
from ..exc import GroupExistsError
from ..model import NAME_PATTERN
from .schema import GroupSchema, MemberSchema

DEFAULT_VALID_ROLES = ["member", "administrator"]


class GroupCollection(Collection):
    schema = GroupSchema
    exist_exc = GroupExistsError

    def get_by_groupname(self, groupname):
        return self.storage.get_by_groupname(self, groupname)


class GroupModel(Model):
    schema = GroupSchema

    def get_user_by_userid(self, userid):
        return self.storage.get_user_by_userid(self, userid)

    def get_user_by_username(self, username):
        return self.storage.get_user_by_username(self, username)

    def members(self):
        members = self.storage.get_members(self, self.identifier)
        active_members = [
            member for member in members if member.data.get("state") == "active"
        ]
        return active_members

    def children(self):
        col = GroupCollection(self.request, self.storage)
        children = col.search(rulez.field["parent"] == self.identifier)
        return children

    def add_members(self, userids):
        self.storage.add_group_members(self, self.identifier, userids)
        for userid in userids:
            self.storage.grant_group_user_role(self, self.identifier, userid, "member")

    def remove_members(self, userids):
        self.storage.remove_group_members(self, self.identifier, userids)

    def get_member_roles(self, userid):
        return self.storage.get_group_user_roles(self, self.identifier, userid)

    def grant_member_role(self, userid, rolename):
        if userid not in [m.userid for m in self.members()]:
            self.add_members([userid])
        valid_roles = self.request.app.get_config(
            "morpfw.valid_roles", DEFAULT_VALID_ROLES
        )
        if rolename not in valid_roles:
            raise exc.InvalidRoleError(rolename)
        self.storage.grant_group_user_role(self, self.identifier, userid, rolename)

    def revoke_member_role(self, userid, rolename):
        if rolename == "member":
            self.remove_members([userid])
            return
        self.storage.revoke_group_user_role(self, self.identifier, userid, rolename)
        if not self.get_member_roles(userid) and self.identifier != "__default__":
            self.remove_members([userid])

    def _links(self):
        links = []
        for m in self.members():
            links.append({"rel": "member", "href": self.request.link(m)})
        return links
