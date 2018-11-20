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
import yaml
import copy

default_settings = yaml.load(
    open(os.path.join(os.path.dirname(__file__), 'default_settings.yml')))


def default_get_identity_policy(settings):
    jwtauth_settings = settings.jwtauth
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

    s = copy.deepcopy(default_settings)
    for k in settings.keys():
        if k in s.keys():
            for j, v in settings[k].items():
                s[k][j] = v
        else:
            s[k] = settings[k]

    settings = s

    # initialize app

    if scan:
        morepath.autoscan()

    app_settings = settings['application']
    for iapp_path in app_settings['mounted_apps']:
        iapp_mod, iapp_clsname = iapp_path.strip().split(':')
        iapp_cls = getattr(__import__(iapp_mod), iapp_clsname)
        iapp_cls.identity_policy()(get_identity_policy)
        iapp_cls.verify_identity()(verify_identity)
        iapp_cls.init_settings(settings)
        iapp_cls._raw_settings = settings
        iapp_cls.commit()

    app.identity_policy()(get_identity_policy)
    app.verify_identity()(verify_identity)
    app.init_settings(settings)
    app._raw_settings = settings

    app.commit()

    if settings['worker']['enabled']:
        celery_settings = settings['worker']['celery_settings']
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
