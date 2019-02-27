from ..app import App
from ...jslcrud.storage.memorystorage import MemoryStorage
from ..model.user import User, UserModel, UserSchema
from ..model.group import Group, GroupModel, GroupSchema
from ..model.apikey import APIKey, APIKeyModel, APIKeySchema
from .interfaces import IStorage
from ..model.base import BaseSchema
from ...jslcrud import errors as cruderrors
from .. import exc
import rulez

DB = {
    'users': {},
    'groups': {},
    'rolemap': {}
}


class UserMemoryStorage(MemoryStorage):
    model = UserModel

    def get_by_email(self, email):
        users = self.search(rulez.field['email'] == email)
        if not users:
            return None
        return users[0]

    def change_password(self, username, new_password):
        user = self.get(username)
        user.data['password'] = new_password

    def get_user_groups(self, username):
        storage = self.request.app.get_authmanager_storage(
            self.request, GroupSchema)
        return storage.get_user_groups(username)

    def validate(self, username, password):
        user = self.get(username)
        return user.data['password'] == password


class APIKeyMemoryStorage(MemoryStorage):
    model = APIKeyModel


class GroupMemoryStorage(MemoryStorage):
    model = GroupModel

    def get_user_groups(self, username):
        res = []
        for gid, group in self.datastore.items():
            group.data.setdefault('attrs', {})
            attrs = group.data['attrs']
            attrs.setdefault('members', [])
            if username in group.data['attrs'].get('members'):
                res.append(group)
        return res

    def get_members(self, groupname):
        group = self.get(groupname)
        userstorage = self.request.app.get_authmanager_storage(
            self.request, UserSchema)
        res = []
        group.data.setdefault('attrs', {})
        attrs = group.data['attrs']
        attrs.setdefault('members', [])
        for m in group.data['attrs'].get('members'):
            res.append(userstorage.get(m))
        return res

    def add_group_members(self, groupname, usernames):
        group = self.get(groupname)
        group.data.setdefault('attrs', {})
        attrs = group.data['attrs']
        attrs.setdefault('members', [])
        for u in usernames:
            if u not in attrs['members']:
                attrs['members'].append(u)
        group.data['attrs'] = attrs

    def remove_group_members(self, groupname, usernames):
        group = self.get(groupname)
        group.data.setdefault('attrs', {})
        attrs = group.data['attrs']
        attrs.setdefault('members', [])
        for u in usernames:
            if u in attrs['members']:
                attrs['members'].remove(u)
        group.data['attrs'] = attrs

    def get_group_user_roles(self, groupname, username):
        rolemap = DB['rolemap']
        rolemap.setdefault(groupname, {})
        rolemap[groupname].setdefault(username, [])
        return rolemap[groupname][username]

    def grant_group_user_role(self, groupname, username, rolename):
        rolemap = DB['rolemap']
        rolemap.setdefault(groupname, {})
        rolemap[groupname].setdefault(username, [])
        if rolename not in rolemap[groupname][username]:
            rolemap[groupname][username].append(rolename)

    def revoke_group_user_role(self, groupname, username, rolename):
        rolemap = DB['rolemap']
        rolemap.setdefault(groupname, {})
        rolemap[groupname].setdefault(username, [])
        if rolename in rolemap[groupname][username]:
            rolemap[groupname][username].remove(rolename)


SINGLETON = {}


def userstorage_factory(request, *args, **kwargs):
    return UserMemoryStorage(request)


@App.authmanager_storage('memorystorage', UserSchema)
def get_userstorage_factory(name, schema):
    return userstorage_factory


def apikeystorage_factory(request, *args, **kwargs):
    return APIKeyMemoryStorage(request)


@App.authmanager_storage('memorystorage', APIKeySchema)
def get_apikeystorage_factory(name, schema):
    return apikeystorage_factory


def groupstorage_factory(request, *args, **kwargs):
    return GroupMemoryStorage(request)


@App.authmanager_storage('memorystorage', GroupSchema)
def get_groupstorage_factory(name, schema):
    return groupstorage_factory
