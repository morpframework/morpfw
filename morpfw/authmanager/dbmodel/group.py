from ...jslcrud.storage.sqlstorage import Base
import sqlalchemy as sa
from sqlalchemy.orm import relationship
import sqlalchemy.orm as saorm
import sqlalchemy_jsonfield as sajson


class Group(Base):

    __tablename__ = 'authmanager_groups'

    groupname = sa.Column(sa.String(length=256))
    attrs = sa.Column(sajson.JSONField)
    memberships = relationship('Membership', cascade='all')


class Membership(Base):

    __tablename__ = 'authmanager_membership'

    group_id = sa.Column(sa.ForeignKey(
        'authmanager_groups.uuid'))
    user_id = sa.Column(sa.ForeignKey(
        'authmanager_users.uuid'))
    created = sa.Column(sa.DateTime)
    sa.UniqueConstraint('group_id', 'user_id')

    roles_assignment = relationship('RoleAssignment', cascade='all')


class RoleAssignment(Base):

    __tablename__ = 'authmanager_roleassignment'

    membership_id = sa.Column(sa.ForeignKey('authmanager_membership.uuid'))
    rolename = sa.Column(sa.String)
    created = sa.Column(sa.DateTime)
    sa.UniqueConstraint('membership_id', 'role_id')
