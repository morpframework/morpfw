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
    plugin_source = sa.Column(sa.String(length=1024))
    attrs = sa.Column(sajson.JSONField)


class APIKey(Base):

    __tablename__ = 'authmanager_apikey'

    userid = sa.Column(GUID)
    label = sa.Column(sa.String(length=256))
    api_identity = sa.Column(sa.String(length=40))
    api_secret = sa.Column(sa.String(length=40))


class Group(Base):

    __tablename__ = 'authmanager_groups'

    groupname = sa.Column(sa.String(length=256))
    attrs = sa.Column(sajson.JSONField)
    memberships = relationship('Membership', cascade='all')


class Membership(Base):

    __tablename__ = 'authmanager_membership'

    group_id = sa.Column(sa.ForeignKey(
        'authmanager_groups.id'))
    user_id = sa.Column(sa.ForeignKey(
        'authmanager_users.id'))
    created = sa.Column(sa.DateTime)
    sa.UniqueConstraint('group_id', 'user_id')

    roles_assignment = relationship('RoleAssignment', cascade='all')


class RoleAssignment(Base):

    __tablename__ = 'authmanager_roleassignment'

    membership_id = sa.Column(sa.ForeignKey('authmanager_membership.id'))
    rolename = sa.Column(sa.String)
    created = sa.Column(sa.DateTime)
    sa.UniqueConstraint('membership_id', 'role_id')
