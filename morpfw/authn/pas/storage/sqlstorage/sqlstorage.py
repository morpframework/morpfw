from ...app import App
from ...user.model import UserSchema, UserModel
from ...group.model import GroupSchema, GroupModel
from ...apikey.model import APIKeyModel, APIKeySchema
from . import dbmodel as db
from morpfw.crud.storage.sqlstorage import SQLStorage
from morpfw.crud import errors as cruderrors
from ..interfaces import IGroupStorage, IUserStorage
import hashlib
import sqlalchemy as sa
from ... import exc


def hash(data):
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


class UserSQLStorage(SQLStorage, IUserStorage):
    model = UserModel
    orm_model = db.User

    def create(self, data):
        data['password'] = hash(data['password'])
        return super(UserSQLStorage, self).create(data)

    def get_userid(self, model):
        return model.uuid

    def get_by_userid(self, userid, as_model=True):
        q = self.session.query(db.User).filter(db.User.uuid == userid)
        u = q.first()
        if not u:
            raise exc.UserDoesNotExistsError(userid)
        if not as_model:
            return u
        return self.model(self.request, self, u)

    def get_by_username(self, username, as_model=True):
        q = self.session.query(db.User).filter(db.User.username == username)
        u = q.first()
        if not u:
            raise exc.UserDoesNotExistsError(username)
        if not as_model:
            return u
        return self.model(self.request, self, u)

    def get_by_email(self, email):
        q = self.session.query(db.User).filter(db.User.email == email)
        u = q.first()
        if not u:
            return None
        return self.model(self.request, self, u)

    def change_password(self, userid, new_password):
        u = self.get_by_userid(userid)
        u.data['password'] = hash(new_password)

    def get_user_groups(self, userid):
        u = self.get_by_userid(userid, as_model=False)
        q = self.session.query(db.Membership).filter(
            db.Membership.user_id == u.id)
        membership = q.all()
        groupstorage = self.request.app.get_storage(GroupModel,
                                                    self.request)
        res = [groupstorage.get_by_id(m.group_id)
               for m in membership]
        return res

    def validate(self, userid, password):
        u = self.get_by_userid(userid)
        return u.data['password'] == hash(password)


class APIKeySQLStorage(SQLStorage):
    model = APIKeyModel
    orm_model = db.APIKey


class GroupSQLStorage(SQLStorage, IGroupStorage):
    model = GroupModel
    orm_model = db.Group

    def get_user_by_userid(self, userid, as_model=True):
        user_storage = self.app.get_storage(UserModel, self.request)
        return user_storage.get_by_userid(userid, as_model)

    def get_user_by_username(self, username, as_model=True):
        user_storage = self.app.get_storage(UserModel, self.request)
        return user_storage.get_by_username(username)

    def get_members(self, groupname):
        q = (self.session.query(db.User)
             .join(db.Membership)
             .join(db.Group)
             .filter(db.Group.groupname == groupname))
        members = []
        user_storage = self.app.get_storage(UserModel, self.request)
        for m in q.all():
            members.append(user_storage.model(self.request, user_storage, m))
        return members

    def add_group_members(self, groupname, userids):
        # FIXME: not using sqlalchemy relations might impact performance
        g = self.session.query(db.Group).filter(
            db.Group.groupname == groupname).first()
        if not g:
            raise ValueError("Group Does Not Exist %s" % groupname)
        gid = g.id
        for userid in userids:
            u = self.get_user_by_userid(userid, as_model=False)
            uid = u.id
            e = self.session.query(db.Membership).filter(
                sa.and_(db.Membership.group_id == gid,
                        db.Membership.user_id == uid)).first()
            if not e:
                m = db.Membership()
                m.group_id = gid
                m.user_id = uid
                self.session.add(m)

    def remove_group_members(self, groupname, userids):
        g = self.session.query(db.Group).filter(
            db.Group.groupname == groupname).first()
        if not g:
            raise exc.GroupDoesNotExistsError(groupname)
        gid = g.id
        for userid in userids:
            u = self.get_user_by_userid(userid, as_model=False)
            uid = u.id
            members = self.session.query(db.Membership).filter(
                sa.and_(db.Membership.group_id == gid,
                        db.Membership.user_id == uid)).all()
            for m in members:
                self.session.delete(m)

    def get_group_user_roles(self, groupname, userid):
        g = self.session.query(db.Group).filter(
            db.Group.groupname == groupname).first()
        if not g:
            raise exc.GroupDoesNotExistsError(groupname)
        gid = g.id
        u = self.get_user_by_userid(userid, as_model=False)
        uid = u.id
        roles = (self.session.query(db.RoleAssignment)
                 .join(db.Membership)
                 .filter(
            sa.and_(db.Membership.group_id == gid,
                    db.Membership.user_id == uid)).all())
        return [r.rolename for r in roles]

    def grant_group_user_role(self, groupname, userid, rolename):
        g = self.session.query(db.Group).filter(
            db.Group.groupname == groupname).first()
        if not g:
            raise exc.GroupDoesNotExistsError(groupname)
        gid = g.id
        u = self.get_user_by_userid(userid, as_model=False)
        uid = u.id
        m = self.session.query(db.Membership).filter(
            sa.and_(db.Membership.group_id == gid,
                    db.Membership.user_id == uid)).first()
        if not m:
            raise exc.MembershipError(userid, groupname)
        ra = self.session.query(db.RoleAssignment).filter(
            db.RoleAssignment.membership_id == m.id,
            db.RoleAssignment.rolename == rolename).first()
        if ra:
            return
        r = db.RoleAssignment()
        r.membership_id = m.id
        r.rolename = rolename
        self.session.add(r)

    def revoke_group_user_role(self, groupname, userid, rolename):
        g = self.session.query(db.Group).filter(
            db.Group.groupname == groupname).first()
        if not g:
            raise exc.GroupDoesNotExistsError(groupname)
        gid = g.id
        u = self.get_user_by_userid(userid, as_model=False)
        uid = u.id
        m = self.session.query(db.Membership).filter(
            sa.and_(db.Membership.group_id == gid,
                    db.Membership.user_id == uid)).first()
        if not m:
            raise exc.MembershipError(userid, groupname)
        ra = self.session.query(db.RoleAssignment).filter(
            db.RoleAssignment.membership_id == m.id,
            db.RoleAssignment.rolename == rolename).first()
        if ra:
            self.session.delete(ra)
