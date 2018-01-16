from ...jslcrud.storage.sqlstorage import Base
import sqlalchemy as sa
import sqlalchemy_jsonfield as sajson


class User(Base):

    __tablename__ = 'authmanager_users'

    username = sa.Column(sa.String(length=256))
    password = sa.Column(sa.String(length=1024))
    attrs = sa.Column(sajson.JSONField)
    state = sa.Column(sa.String(length=64))
    created = sa.Column(sa.DateTime)
    last_modified = sa.Column(sa.DateTime)
