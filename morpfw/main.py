import reg
import morepath
from .app import SQLApp, Session, BaseApp
from .sql import Base
import os
from zope.sqlalchemy import register as register_session
from .authmanager.authpolicy import JWTWithAPIKeyIdentityPolicy
from more.basicauth import BasicAuthIdentityPolicy
from .exc import ConfigurationError
import transaction
import sqlalchemy
from celery import Celery


def get_identity_policy(settings):
    jwtauth_settings = getattr(settings, 'jwtauth', None)
    if jwtauth_settings:
        # Pass the settings dictionary to the identity policy.
        return JWTWithAPIKeyIdentityPolicy(**jwtauth_settings.__dict__.copy())
    raise Exception('JWTAuth configuration is not set')


def verify_identity(app, identity):
    # As we use a token based authentication
    # we can trust the claimed identity.
    return True


@reg.dispatch(reg.match_class('app', lambda app, *args, **kwargs: app))
def create_app(app, settings, scan=True,
               get_identity_policy=get_identity_policy,
               verify_identity=verify_identity, **kwargs):
    raise NotImplementedError


@create_app.register(app=BaseApp)
def create_baseapp(app, settings, scan=True,
                   get_identity_policy=get_identity_policy,
                   verify_identity=verify_identity, **kwargs):
    app.identity_policy()(get_identity_policy)
    app.verify_identity()(verify_identity)
    # initialize app
    app.init_settings(settings)
    app._raw_settings = settings
    celery_settings = settings['celery']
    app.celery.conf.update(**celery_settings)
    morepath.commit(app)
    if scan:
        morepath.autoscan()
        app.commit()
    application = app()
    return application
