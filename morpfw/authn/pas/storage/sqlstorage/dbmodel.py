import sqlalchemy as sa
import sqlalchemy.orm as saorm
import sqlalchemy_jsonfield as sajson
from morpfw.crud.storage.sqlstorage import GUID, Base
from sqlalchemy.orm import relationship


class User(Base):

    __tablename__ = "authmanager_users"

    username = sa.Column(sa.String(length=256))
    email = sa.Column(sa.String)
    password = sa.Column(sa.String(length=1024))
    source = sa.Column(sa.String(length=1024))
    nonce = sa.Column(sa.String(length=24))
    timezone = sa.Column(sa.String(length=124))
    is_administrator = sa.Column(sa.Boolean())


class APIKey(Base):

    __tablename__ = "authmanager_apikey"

    userid = sa.Column(GUID)
    name = sa.Column(sa.String(length=256))
    api_identity = sa.Column(sa.String(length=64))
    api_secret = sa.Column(sa.String(length=128))


class Group(Base):

    __tablename__ = "authmanager_groups"

    parent = sa.Column(sa.String(length=256))
    groupname = sa.Column(sa.String(length=256))
    memberships = relationship("Membership", cascade="all")


class Membership(Base):

    __tablename__ = "authmanager_membership"

    group_id = sa.Column(sa.ForeignKey("authmanager_groups.id"))
    user_id = sa.Column(sa.ForeignKey("authmanager_users.id"))
    sa.UniqueConstraint("group_id", "user_id", "deleted")

    roles_assignment = relationship("RoleAssignment", cascade="all")


class RoleAssignment(Base):

    __tablename__ = "authmanager_roleassignment"

    membership_id = sa.Column(sa.ForeignKey("authmanager_membership.id"))
    rolename = sa.Column(sa.String)
    sa.UniqueConstraint("membership_id", "role_id", "deleted")
