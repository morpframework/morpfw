from ..app import App
from ..model.user import User, UserSchema, UserModel
from ..model.group import Group, GroupSchema, GroupModel
from ..model.base import BaseSchema
from ..model.apikey import APIKeyModel, APIKeySchema, APIKey
from ...jslcrud.storage.sqlstorage import SQLStorage
from ...jslcrud import errors as cruderrors
from .. import dbmodel as db
from .interfaces import IStorage
import hashlib
import sqlalchemy as sa
from .. import exc


def hash(data):
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


class UserSQLStorage(SQLStorage):
    model = UserModel
    orm_model = User

    def create(self, data):
        data['password'] = hash(data['password'])
        return super(UserSQLStorage, self).create(data)

    def get_by_email(self, email):
        q = self.session.query(db.User).filter(
            db.User.email == email, db.User.deleted.is_(None))
        u = q.first()
        if not u:
            return None
        return self.model(self.request, self, u)

    def change_password(self, username, new_password):
        q = self.session.query(db.User).filter(
            db.User.username == username, db.User.deleted.is_(None))
        u = q.first()
        if not u:
            raise ValueError("Unknown User %s" % username)
        u.password = hash(new_password)

    def get_user_groups(self, username):
        q = self.session.query(db.User).filter(
            db.User.username == username, db.User.deleted.is_(None))
        u = q.first()
        if not u:
            raise ValueError("Unknown user %s" % username)
        q = self.session.query(db.Membership).filter(
            db.Membership.user_id == u.uuid)
        membership = q.all()
        groupstorage = self.request.app.get_authmanager_storage(
            self.request, GroupSchema)
        res = [groupstorage.get_by_uuid(m.group_id)
               for m in membership]
        filtered = [m for m in res if not m.data['deleted']]
        return filtered

    def validate(self, username, password):

        q = self.session.query(db.User).filter(
            db.User.username == username, db.User.deleted.is_(None))
        u = q.first()
        if not u:
            raise ValueError("Unknown User %s" % username)
        return u.password == hash(password)


class APIKeySQLStorage(SQLStorage):
    model = APIKeyModel
    orm_model = APIKey


class GroupSQLStorage(SQLStorage):
    model = GroupModel
    orm_model = Group

    def get_members(self, groupname):
        q = (self.session.query(db.User)
             .join(db.Membership)
             .join(db.Group)
             .filter(db.Group.groupname == groupname, db.User.deleted.is_(None)))
        members = []
        user_storage = UserSQLStorage(self.request)
        for m in q.all():
            members.append(UserModel(self.request, user_storage, m))
        return members

    def add_group_members(self, groupname, usernames):
        # FIXME: not using sqlalchemy relations might impact performance
        g = self.session.query(db.Group).filter(
            db.Group.groupname == groupname, db.Group.deleted.is_(None)).first()
        if not g:
            raise ValueError("Group Does Not Exist %s" % groupname)
        gid = g.uuid
        for username in usernames:
            u = self.session.query(db.User).filter(
                db.User.username == username, db.User.deleted.is_(None)).first()
            if not u:
                raise ValueError("User Does Not Exist %s" % username)
            uid = u.uuid
            e = self.session.query(db.Membership).filter(
                sa.and_(db.Membership.group_id == gid,
                        db.Membership.user_id == uid)).first()
            if not e:
                m = db.Membership()
                m.group_id = gid
                m.user_id = uid
                self.session.add(m)

    def remove_group_members(self, groupname, usernames):
        g = self.session.query(db.Group).filter(
            db.Group.groupname == groupname, db.Group.deleted.is_(None)).first()
        if not g:
            raise exc.GroupDoesNotExistsError(groupname)
        gid = g.uuid
        for username in usernames:
            u = self.session.query(db.User).filter(
                db.User.username == username, db.User.deleted.is_(None)).first()
            if not u:
                raise exc.UserDoesNotExistsError(username)
            uid = u.uuid
            members = self.session.query(db.Membership).filter(
                sa.and_(db.Membership.group_id == gid,
                        db.Membership.user_id == uid)).all()
            for m in members:
                self.session.delete(m)

    def get_group_user_roles(self, groupname, username):
        g = self.session.query(db.Group).filter(
            db.Group.groupname == groupname, db.Group.deleted.is_(None)).first()
        if not g:
            raise exc.GroupDoesNotExistsError(groupname)
        gid = g.uuid
        u = self.session.query(db.User).filter(
            db.User.username == username, db.User.deleted.is_(None)).first()
        if not u:
            raise exc.UserDoesNotExistsError(username)
        uid = u.uuid
        roles = (self.session.query(db.RoleAssignment)
                 .join(db.Membership)
                 .filter(
            sa.and_(db.Membership.group_id == gid,
                    db.Membership.user_id == uid)).all())
        return [r.rolename for r in roles]

    def grant_group_user_role(self, groupname, username, rolename):
        g = self.session.query(db.Group).filter(
            db.Group.groupname == groupname, db.Group.deleted.is_(None)).first()
        if not g:
            raise exc.GroupDoesNotExistsError(groupname)
        gid = g.uuid
        u = self.session.query(db.User).filter(
            db.User.username == username, db.User.deleted.is_(None)).first()
        if not u:
            raise exc.UserDoesNotExistsError(username)
        uid = u.uuid
        m = self.session.query(db.Membership).filter(
            sa.and_(db.Membership.group_id == gid,
                    db.Membership.user_id == uid)).first()
        if not m:
            raise exc.MembershipError(username, groupname)
        ra = self.session.query(db.RoleAssignment).filter(
            db.RoleAssignment.membership_id == m.uuid,
            db.RoleAssignment.rolename == rolename).first()
        if ra:
            return
        r = db.RoleAssignment()
        r.membership_id = m.uuid
        r.rolename = rolename
        self.session.add(r)

    def revoke_group_user_role(self, groupname, username, rolename):
        g = self.session.query(db.Group).filter(
            db.Group.groupname == groupname, db.Group.deleted.is_(None)).first()
        if not g:
            raise exc.GroupDoesNotExistsError(groupname)
        gid = g.uuid
        u = self.session.query(db.User).filter(
            db.User.username == username, db.User.deleted.is_(None)).first()
        if not u:
            raise exc.UserDoesNotExistsError(username)
        uid = u.uuid
        m = self.session.query(db.Membership).filter(
            sa.and_(db.Membership.group_id == gid,
                    db.Membership.user_id == uid)).first()
        if not m:
            raise exc.MembershipError(username, groupname)
        ra = self.session.query(db.RoleAssignment).filter(
            db.RoleAssignment.membership_id == m.uuid,
            db.RoleAssignment.rolename == rolename).first()
        if ra:
            self.session.delete(ra)


def userstorage_factory(request, *args, **kwargs):
    return UserSQLStorage(request)


def apikeystorage_factory(request, *args, **kwargs):
    return APIKeySQLStorage(request)


@App.authmanager_storage('sqlstorage', APIKeySchema)
def get_apikeystorage_factory(name, schema):
    return apikeystorage_factory


@App.authmanager_storage('sqlstorage', UserSchema)
def get_userstorage_factory(name, schema):
    return userstorage_factory


def groupstorage_factory(request, *args, **kwargs):
    return GroupSQLStorage(request)


@App.authmanager_storage('sqlstorage', GroupSchema)
def get_groupstorage_factory(name, schema):
    return groupstorage_factory
