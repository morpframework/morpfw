import importlib
import reg
import morepath
from .app import SQLApp, Session, BaseApp
from .sql import Base
import os
from zope.sqlalchemy import register as register_session
from more.basicauth import BasicAuthIdentityPolicy
from .exc import ConfigurationError
import transaction
import sqlalchemy
from celery import Celery
import yaml
import copy

default_settings = yaml.load(
    open(os.path.join(os.path.dirname(__file__), 'default_settings.yml')))


@reg.dispatch(reg.match_class('app', lambda app, *args, **kwargs: app))
def create_app(app, settings, scan=True, **kwargs):
    raise NotImplementedError


@create_app.register(app=BaseApp)
def create_baseapp(app, settings, scan=True, **kwargs):

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

    authnpol_mod, authnpol_clsname = (
        app_settings['authn_policy'].strip().split(':'))
    authnpolicy = getattr(importlib.import_module(
        authnpol_mod), authnpol_clsname)

    authnzprv_mod, authnzprv_factory = (
        app_settings['authnz_provider'].strip().split(':'))
    authnz_provider = getattr(importlib.import_module(
        authnzprv_mod), authnzprv_factory)

    get_identity_policy = authnpolicy.get_identity_policy
    verify_identity = authnpolicy.verify_identity

    for iapp in app_settings['mounted_apps']:
        iapp_path = iapp['app']
        iapp_mod, iapp_clsname = iapp_path.strip().split(':')
        iapp_cls = getattr(importlib.import_module(iapp_mod), iapp_clsname)

        if iapp.get('authn_policy', None):
            iapp_authnpol_mod, iapp_authnpol_clsname = (
                iapp['authn_policy'].strip().split(':'))
            iapp_authnpolicy = getattr(importlib.import_module(
                iapp_authnpol_mod), iapp_authnpol_clsname)
            iapp_get_identity_policy = iapp_authnpolicy.get_identity_policy
            iapp_verify_identity = iapp_authnpolicy.verify_identity
            iapp_cls.identity_policy()(iapp_get_identity_policy)
            iapp_cls.verify_identity()(iapp_verify_identity)
        else:
            iapp_cls.identity_policy()(get_identity_policy)
            iapp_cls.verify_identity()(verify_identity)

        iapp_cls.init_settings(settings)
        iapp_cls._raw_settings = settings
        iapp_cls.commit()

    app.identity_policy()(get_identity_policy)
    app.verify_identity()(verify_identity)
    app.authnz_provider()(lambda: authnz_provider())
    app.init_settings(settings)
    app._raw_settings = settings

    if settings['application']['development_mode']:
        os.environ['MOREPATH_TEMPLATE_AUTO_RELOAD'] = "1"

    app.commit()

    if settings['worker']['enabled']:
        celery_settings = settings['worker']['celery_settings']
        app.celery.conf.update(**celery_settings)
    application = app()
    return application


@create_app.register(app=SQLApp)
def create_sqlapp(app, settings, scan=True, **kwargs):

    application = create_baseapp(app=app, settings=settings, scan=scan,
                                 **kwargs)

    application.initdb()
    return application


def run(app, settings, host='127.0.0.1', port=5000, ignore_cli=True):
    application = create_app(app, settings)
    morepath.run(application, host=host, port=port, ignore_cli=ignore_cli)
