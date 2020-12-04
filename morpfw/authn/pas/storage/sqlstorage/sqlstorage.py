import hashlib

import sqlalchemy as sa
from morpfw.crud import errors as cruderrors
from morpfw.crud.storage.sqlstorage import SQLStorage

from ... import exc
from ...apikey.model import APIKeyModel, APIKeySchema
from ...app import App
from ...group.model import GroupCollection, GroupModel, GroupSchema
from ...user.model import UserCollection, UserModel, UserSchema
from ..interfaces import IGroupStorage, IUserStorage
from . import dbmodel as db


def hash(data):
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


class UserSQLStorage(SQLStorage, IUserStorage):
    model = UserModel
    orm_model = db.User

    def create(self, collection, data):
        data["password"] = hash(data["password"])
        return super(UserSQLStorage, self).create(collection, data)

    def get_userid(self, model):
        return model.uuid

    def get_by_userid(self, collection, userid, as_model=True):
        q = self.session.query(db.User).filter(db.User.uuid == userid)
        u = q.first()
        if not u:
            return None
        if not as_model:
            return u
        return self.model(self.request, collection, u)

    def get_by_username(self, collection, username, as_model=True):
        q = self.session.query(db.User).filter(
            sa.and_(db.User.username == username, db.User.deleted.is_(None))
        )
        u = q.first()
        if not u:
            return None
        if not as_model:
            return u
        return self.model(self.request, collection, u)

    def get_by_email(self, collection, email):
        q = self.session.query(db.User).filter(
            sa.and_(db.User.email == email, db.User.deleted.is_(None))
        )
        u = q.first()
        if not u:
            return None
        return self.model(self.request, collection, u)

    def change_password(self, collection, userid, new_password):
        u = self.get_by_userid(collection, userid)
        u.data["password"] = hash(new_password)

    def get_user_groups(self, collection, userid):
        u = self.get_by_userid(collection, userid, as_model=False)
        q = (
            self.session.query(db.Membership)
            .join(db.Group)
            .filter(sa.and_(db.Membership.user_id == u.id, db.Group.deleted.is_(None)))
        )
        membership = q.all()
        groupstorage = self.request.app.get_storage(GroupModel, self.request)
        gcol = GroupCollection(self.request, groupstorage)
        res = [groupstorage.get_by_id(gcol, m.group_id) for m in membership]
        filtered = [m for m in res if not m.data["deleted"]]
        return filtered

    def validate(self, collection, userid, password):
        u = self.get_by_userid(collection, userid)
        return u.data["password"] == hash(password)

    def vacuum(self):
        roleassignment_delete = db.RoleAssignment.__table__.delete().where(
            db.User.deleted.isnot(None)
        )

        membership_delete = db.Membership.__table__.delete().where(
            db.User.deleted.isnot(None)
        )
        self.session.execute(roleassignment_delete)
        self.session.execute(membership_delete)
        return super().vacuum()


class APIKeySQLStorage(SQLStorage):
    model = APIKeyModel
    orm_model = db.APIKey


class GroupSQLStorage(SQLStorage, IGroupStorage):
    model = GroupModel
    orm_model = db.Group

    def get_user_by_userid(self, collection, userid, as_model=True):
        user_storage = self.app.get_storage(UserModel, self.request)
        user_collection = UserCollection(self.request, user_storage)
        return user_storage.get_by_userid(user_collection, userid, as_model)

    def get_user_by_username(self, collection, username, as_model=True):
        user_storage = self.app.get_storage(UserModel, self.request)
        user_collection = UserCollection(self.request, user_storage)
        return user_storage.get_by_username(user_collection, username, as_model)

    def get_members(self, collection, groupid):
        q = (
            self.session.query(db.User)
            .join(db.Membership)
            .join(db.Group)
            .filter(
                sa.and_(
                    db.Group.uuid == groupid,
                    db.Group.deleted.is_(None),
                    db.User.deleted.is_(None),
                )
            )
        )
        members = []
        user_storage = self.app.get_storage(UserModel, self.request)
        user_collection = UserCollection(self.request, user_storage)

        for m in q.all():
            members.append(user_storage.model(self.request, user_collection, m))
        return members

    def add_group_members(self, collection, groupid, userids):
        # FIXME: not using sqlalchemy relations might impact performance
        g = (
            self.session.query(db.Group)
            .filter(sa.and_(db.Group.uuid == groupid, db.Group.deleted.is_(None)))
            .first()
        )
        if not g:
            raise ValueError("Group Does Not Exist %s" % groupid)
        gid = g.id
        for userid in userids:
            u = self.get_user_by_userid(collection, userid, as_model=False)
            uid = u.id
            e = (
                self.session.query(db.Membership)
                .join(db.Group)
                .filter(
                    sa.and_(
                        db.Membership.group_id == gid,
                        db.Membership.user_id == uid,
                        db.Group.deleted.is_(None),
                    )
                )
                .first()
            )
            if not e:
                m = db.Membership()
                m.group_id = gid
                m.user_id = uid
                self.session.add(m)

    def remove_group_members(self, collection, groupid, userids):
        g = (
            self.session.query(db.Group)
            .filter(sa.and_(db.Group.uuid == groupid, db.Group.deleted.is_(None)))
            .first()
        )
        if not g:
            raise exc.GroupDoesNotExistsError(groupid)
        gid = g.id
        for userid in userids:
            u = self.get_user_by_userid(collection, userid, as_model=False)
            uid = u.id
            members = (
                self.session.query(db.Membership)
                .join(db.Group)
                .filter(
                    sa.and_(
                        db.Membership.group_id == gid,
                        db.Membership.user_id == uid,
                        db.Group.deleted.is_(None),
                    )
                )
                .all()
            )
            for m in members:
                self.session.delete(m)

    def get_group_user_roles(self, collection, groupid, userid):
        g = (
            self.session.query(db.Group)
            .filter(sa.and_(db.Group.uuid == groupid, db.Group.deleted.is_(None)))
            .first()
        )
        if not g:
            raise exc.GroupDoesNotExistsError(groupid)
        gid = g.id
        u = self.get_user_by_userid(collection, userid, as_model=False)
        uid = u.id
        roles = (
            self.session.query(db.RoleAssignment)
            .join(db.Membership)
            .join(db.Group)
            .filter(
                sa.and_(
                    db.Membership.group_id == gid,
                    db.Membership.user_id == uid,
                    db.Group.deleted.is_(None),
                )
            )
            .all()
        )
        return [r.rolename for r in roles]

    def get_by_groupname(self, collection, groupname):
        g = (
            self.session.query(db.Group)
            .filter(
                sa.and_(db.Group.groupname == groupname, db.Group.deleted.is_(None))
            )
            .first()
        )
        if not g:
            return None
        return self.model(self.request, collection, g)

    def grant_group_user_role(self, collection, groupid, userid, rolename):
        g = (
            self.session.query(db.Group)
            .filter(sa.and_(db.Group.uuid == groupid, db.Group.deleted.is_(None)))
            .first()
        )
        if not g:
            raise exc.GroupDoesNotExistsError(groupid)
        gid = g.id
        u = self.get_user_by_userid(collection, userid, as_model=False)
        uid = u.id
        m = (
            self.session.query(db.Membership)
            .join(db.Group)
            .filter(
                sa.and_(
                    db.Membership.group_id == gid,
                    db.Membership.user_id == uid,
                    db.Group.deleted.is_(None),
                )
            )
            .first()
        )
        if not m:
            raise exc.MembershipError(userid, groupid)
        ra = (
            self.session.query(db.RoleAssignment)
            .filter(
                db.RoleAssignment.membership_id == m.id,
                db.RoleAssignment.rolename == rolename,
            )
            .first()
        )
        if ra:
            return
        r = db.RoleAssignment()
        r.membership_id = m.id
        r.rolename = rolename
        self.session.add(r)

    def revoke_group_user_role(self, collection, groupid, userid, rolename):
        g = (
            self.session.query(db.Group)
            .filter(sa.and_(db.Group.uuid == groupid, db.Group.deleted.is_(None)))
            .first()
        )
        if not g:
            raise exc.GroupDoesNotExistsError(groupid)
        gid = g.id
        u = self.get_user_by_userid(collection, userid, as_model=False)
        uid = u.id
        m = (
            self.session.query(db.Membership)
            .join(db.Group)
            .filter(
                sa.and_(
                    db.Membership.group_id == gid,
                    db.Membership.user_id == uid,
                    db.Group.deleted.is_(None),
                )
            )
            .first()
        )
        if not m:
            raise exc.MembershipError(userid, groupid)
        ra = (
            self.session.query(db.RoleAssignment)
            .filter(
                db.RoleAssignment.membership_id == m.id,
                db.RoleAssignment.rolename == rolename,
            )
            .first()
        )
        if ra:
            self.session.delete(ra)

    def vacuum(self):
        roleassignment_delete = db.RoleAssignment.__table__.delete().where(
            db.Group.deleted.isnot(None)
        )
        membership_delete = db.Membership.__table__.delete().where(
            db.Group.deleted.isnot(None)
        )
        self.session.execute(roleassignment_delete)
        self.session.execute(membership_delete)
        return super().vacuum()
