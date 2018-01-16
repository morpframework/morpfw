from .app import App
import morepath
import os
import sqlalchemy
from ..jslcrud.storage.sqlstorage import Base
from sqlalchemy.orm import sessionmaker
from zope.sqlalchemy import register as register_session
from .model.user import UserModel, UserCollection
from .model.group import GroupModel, GroupCollection

Session = sessionmaker()


def create_app(app, settings, sqlalchemy_session=Session,
               sqlalchemy_bases=None, get_identity_policy=None,
               verify_identity=None):
    register_session(sqlalchemy_session)
    sqlalchemy_bases = sqlalchemy_bases or [Base]
    # initialize SQLAlchemy
    if 'sqlalchemy' in settings:
        cwd = os.getcwd()
        engine = sqlalchemy.create_engine(
            settings['sqlalchemy']['dburi'] % {'here': cwd})
        sqlalchemy_session.configure(bind=engine)

    if get_identity_policy is not None:
        app.identity_policy()(get_identity_policy)

    if verify_identity is not None:
        app.verify_identity()(verify_identity)

    # initialize app
    app.init_settings(settings)
    morepath.commit(app)
    morepath.autoscan()
    app.commit()
    application = app()

    # create tables
    if 'sqlalchemy' in settings:
        for base in sqlalchemy_bases:
            base.metadata.create_all(engine)

    return application
