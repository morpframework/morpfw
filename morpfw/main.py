import reg
import morepath
from .app import SQLApp, Session, BaseApp
from .sql import Base
import os
from zope.sqlalchemy import register as register_session
from .auth.authpolicy import JWTWithAPIKeyIdentityPolicy
from more.basicauth import BasicAuthIdentityPolicy
from .exc import ConfigurationError
import transaction
import sqlalchemy
from celery import Celery


def default_get_identity_policy(settings):
    jwtauth_settings = getattr(settings, 'jwtauth', None)
    if jwtauth_settings:
        # Pass the settings dictionary to the identity policy.
        return JWTWithAPIKeyIdentityPolicy(**jwtauth_settings.__dict__.copy())
    raise Exception('JWTAuth configuration is not set')


def default_verify_identity(app, identity):
    # As we use a token based authentication
    # we can trust the claimed identity.
    return True


@reg.dispatch(reg.match_class('app', lambda app, *args, **kwargs: app))
def create_app(app, settings, scan=True,
               get_identity_policy=default_get_identity_policy,
               verify_identity=default_verify_identity, **kwargs):
    raise NotImplementedError


@create_app.register(app=BaseApp)
def create_baseapp(app, settings, scan=True,
                   get_identity_policy=default_get_identity_policy,
                   verify_identity=default_verify_identity, **kwargs):
    app.identity_policy()(get_identity_policy)
    app.verify_identity()(verify_identity)
    # initialize app

#	morp_settings = settings.get('morp', {})
#	for iapp_path in morp_settings.get('additional_apps', []):
#		iapp_mod, iapp_clsname = iapp_path.strip().split(':')
#		iapp_cls = getattr(__import__(iapp_mod), iapp_clsname)
#		iapp_cls.init_settings(settings)

    app.init_settings(settings)
    app._raw_settings = settings

    if scan:
        morepath.autoscan()
        app.commit()

    if settings.get('morp', {}).get('use_celery', False):
        celery_settings = settings['celery']
        app.celery.conf.update(**celery_settings)
    application = app()
    return application


@create_app.register(app=SQLApp)
def create_sqlapp(app, settings, scan=True,
                  get_identity_policy=default_get_identity_policy,
                  verify_identity=default_verify_identity, **kwargs):

    application = create_baseapp(app=app, settings=settings, scan=scan,
                                 get_identity_policy=get_identity_policy,
                                 verify_identity=verify_identity, **kwargs)

    application.initdb()
    return application
