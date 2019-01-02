from morpfw.crud.storage.sqlstorage import Base
from morpfw.crud.storage.sqlstorage import GUID
import sqlalchemy as sa
from sqlalchemy.orm import relationship
import sqlalchemy.orm as saorm
import sqlalchemy_jsonfield as sajson


class User(Base):

    __tablename__ = 'authmanager_users'

    username = sa.Column(sa.String(length=256))
    email = sa.Column(sa.String)
    password = sa.Column(sa.String(length=1024))
    source = sa.Column(sa.String(length=1024))


class APIKey(Base):

    __tablename__ = 'authmanager_apikey'

    userid = sa.Column(GUID)
    label = sa.Column(sa.String(length=256))
    api_identity = sa.Column(sa.String(length=40))
    api_secret = sa.Column(sa.String(length=40))


class Group(Base):

    __tablename__ = 'authmanager_groups'

    groupname = sa.Column(sa.String(length=256))
    memberships = relationship('Membership', cascade='all')


class Membership(Base):

    __tablename__ = 'authmanager_membership'

    group_id = sa.Column(sa.ForeignKey(
        'authmanager_groups.id'))
    user_id = sa.Column(sa.ForeignKey(
        'authmanager_users.id'))
    sa.UniqueConstraint('group_id', 'user_id')

    roles_assignment = relationship('RoleAssignment', cascade='all')


class RoleAssignment(Base):

    __tablename__ = 'authmanager_roleassignment'

    membership_id = sa.Column(sa.ForeignKey('authmanager_membership.id'))
    rolename = sa.Column(sa.String)
    sa.UniqueConstraint('membership_id', 'role_id')
