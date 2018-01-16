from ...jslcrud.storage.sqlstorage import Base
import sqlalchemy as sa


class APIKey(Base):

    __tablename__ = 'authmanager_apikey'

    username = sa.Column(sa.String(256))
    label = sa.Column(sa.String(length=256))
    api_identity = sa.Column(sa.String(length=40))
    api_secret = sa.Column(sa.String(length=40))
