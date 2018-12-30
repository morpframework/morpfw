from ..app import App
from morpfw.crud.storage.memorystorage import MemoryStorage
from ..user.model import UserModel, UserSchema
from ..group.model import GroupModel, GroupSchema
from ..apikey.model import APIKeyModel, APIKeySchema
from .interfaces import IUserStorage, IGroupStorage
from morpfw.crud import errors as cruderrors
from .. import exc
import rulez

DB: dict = {
    'users': {},
    'groups': {},
    'rolemap': {}
}


class UserMemoryStorage(MemoryStorage, IUserStorage):
    model = UserModel

    def get_userid(self, model):
        return model.uuid

    def get_by_email(self, email):
        users = self.search(rulez.field['email'] == email)
        if not users:
            return None
        return users[0]

    def get_by_userid(self, userid):
        users = self.search(rulez.field['uuid'] == userid)
        if not users:
            return None
        return users[0]

    def get_by_username(self, username):
        users = self.search(rulez.field['username'] == username)
        if not users:
            return None
        return users[0]

    def change_password(self, userid, new_password):
        user = self.get_by_userid(userid)
        user.data['password'] = new_password

    def get_user_groups(self, userid):
        storage = self.request.app.root.get_authnz_provider().get_authn_storage(
            self.request, GroupSchema)
        return storage.get_user_groups(userid)

    def validate(self, userid, password):
        user = self.get_by_userid(userid)
        return user.data['password'] == password


class APIKeyMemoryStorage(MemoryStorage):
    model = APIKeyModel


class GroupMemoryStorage(MemoryStorage, IGroupStorage):
    model = GroupModel

    def get_user_by_userid(self, userid, as_model=True):
        user_storage = self.app.get_authn_storage(self.request, UserSchema)
        return user_storage.get_by_userid(userid, as_model)

    def get_user_by_username(self, username, as_model=True):
        user_storage = self.app.get_authn_storage(self.request, UserSchema)
        return user_storage.get(username)

    def get_user_groups(self, userid):
        res = []
        for gid, group in self.datastore.items():
            if userid in group.data['attrs'].get('members'):
                res.append(group)
        return res

    def get_members(self, groupname):
        group = self.get(groupname)
        userstorage = self.request.app.root.get_authnz_provider().get_authn_storage(
            self.request, UserSchema)
        res = []
        group.data.setdefault('attrs', {})
        attrs = group.data['attrs']
        attrs.setdefault('members', [])
        for m in group.data['attrs'].get('members'):
            res.append(userstorage.get_by_userid(m))
        return res

    def add_group_members(self, groupname, userids):
        group = self.get(groupname)
        group.data.setdefault('attrs', {})
        attrs = group.data['attrs']
        attrs.setdefault('members', [])
        for u in userids:
            if u not in attrs['members']:
                attrs['members'].append(u)
        group.data['attrs'] = attrs

    def remove_group_members(self, groupname, userids):
        group = self.get(groupname)
        group.data.setdefault('attrs', {})
        attrs = group.data['attrs']
        attrs.setdefault('members', [])
        for u in userids:
            if u in attrs['members']:
                attrs['members'].remove(u)
        group.data['attrs'] = attrs

    def get_group_user_roles(self, groupname, userid):
        rolemap = DB['rolemap']
        rolemap.setdefault(groupname, {})
        rolemap[groupname].setdefault(userid, [])
        return rolemap[groupname][userid]

    def grant_group_user_role(self, groupname, userid, rolename):
        rolemap = DB['rolemap']
        rolemap.setdefault(groupname, {})
        rolemap[groupname].setdefault(userid, [])
        if rolename not in rolemap[groupname][userid]:
            rolemap[groupname][userid].append(rolename)

    def revoke_group_user_role(self, groupname, userid, rolename):
        rolemap = DB['rolemap']
        rolemap.setdefault(groupname, {})
        rolemap[groupname].setdefault(userid, [])
        if rolename in rolemap[groupname][userid]:
            rolemap[groupname][userid].remove(rolename)


SINGLETON: dict = {}


def userstorage_factory(request, *args, **kwargs):
    return UserMemoryStorage(request)


@App.authn_storage('memorystorage', UserSchema)
def get_userstorage_factory(name, schema):
    return userstorage_factory


def apikeystorage_factory(request, *args, **kwargs):
    return APIKeyMemoryStorage(request)


@App.authn_storage('memorystorage', APIKeySchema)
def get_apikeystorage_factory(name, schema):
    return apikeystorage_factory


def groupstorage_factory(request, *args, **kwargs):
    return GroupMemoryStorage(request)


@App.authn_storage('memorystorage', GroupSchema)
def get_groupstorage_factory(name, schema):
    return groupstorage_factory
