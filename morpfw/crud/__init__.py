import morepath
from .app import App
from . import subscribers
from .app import Session
import argparse
import yaml
import sqlalchemy
import os
from .model import Collection, Model
from .rulesadapter import Adapter
from .schema import Schema
from .model import StateMachine
from .util import resolve_model
from .app import App
from .storage.sqlstorage import SQLStorage
from zope.sqlalchemy import register as register_session


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--settings', default='settings.yml')
    args = parser.parse_args()
    with open(args.settings) as cf:
        settings = yaml.load(cf)

    application = create_app(App, settings)

    # start app
    morepath.run(application)


def create_app(app, settings, sqlalchemy_session=Session,
               sqlalchemy_bases=None):
    sqlalchemy_bases = sqlalchemy_bases or []
    register_session(sqlalchemy_session)
    # initialize SQLAlchemy
    if 'sqlalchemy' in settings:
        cwd = os.getcwd()
        engine = sqlalchemy.create_engine(
            settings['sqlalchemy']['dburi'] % {'here': cwd})
        sqlalchemy_session.configure(bind=engine)

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


if __name__ == '__main__':
    run()
