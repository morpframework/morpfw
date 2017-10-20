import reg
import morepath
from .app import SQLApp, Session, BaseApp
from .sql import Base
import os
from zope.sqlalchemy import register as register_session
from more.jwtauth import JWTIdentityPolicy
from more.basicauth import BasicAuthIdentityPolicy
from authmanager.model.user import UserCollection, UserSchema
from authmanager.model.group import GroupCollection, GroupSchema
from authmanager.exc import UserExistsError
from morp.exc import ConfigurationError
import transaction
import sqlalchemy
from celery import Celery


def get_identity_policy(settings):
    jwtauth_settings = getattr(settings, 'jwtauth', None)
    if jwtauth_settings:
        # Pass the settings dictionary to the identity policy.
        return JWTIdentityPolicy(**jwtauth_settings.__dict__.copy())
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
    if 'morp' in settings.keys():
        morpsettings = settings['morp']
        if morpsettings.get('use_celery', False):
            celery_settings = morpsettings.get('celery', {
                'broker_url': 'redis://',
                'result_backend': 'redis://'
            }).copy()

            for exclude in ['metastore', 'metastore_opts']:
                if exclude in celery_settings.keys():
                    del celery_settings[exclude]
            app.celery.conf.update(**celery_settings)
    morepath.commit(app)
    if scan:
        morepath.autoscan()
        app.commit()
    application = app()
    return application


@create_app.register(app=SQLApp)
def create_sqlapp(app, settings, scan=True, get_identity_policy=get_identity_policy,
                  verify_identity=verify_identity, **kwargs):

    sqlalchemy_session = kwargs.get('sqalchemy_session', Session)
    register_session(sqlalchemy_session)

    # initialize SQLAlchemy
    if 'sqlalchemy' not in settings:
        raise ConfigurationError('SQLAlchemy settings not found')
    if 'sqlalchemy' in settings:
        cwd = os.environ.get('MORP_WORKDIR', os.getcwd())
        os.chdir(cwd)
        dburi = settings['sqlalchemy']['dburi'] % {'here': cwd}
        engine = sqlalchemy.create_engine(dburi)
        sqlalchemy_session.configure(bind=engine)

    app.identity_policy()(get_identity_policy)

    app.verify_identity()(verify_identity)
    # initialize app
    app.init_settings(settings)
    app._raw_settings = settings
    if 'morp' in settings.keys():
        morpsettings = settings['morp']

        if morpsettings.get('use_celery', False):
            celery_settings = morpsettings.get('celery', {
                'broker_url': 'redis://',
                'result_backend': 'redis://'
            }).copy()

            for exclude in ['metastore', 'metastore_opts']:
                if exclude in celery_settings.keys():
                    del celery_settings[exclude]
            app.celery.conf.update(**celery_settings)

    morepath.commit(app)
    if scan:
        morepath.autoscan()
        app.commit()
    application = app()

    # create tables
    if 'sqlalchemy' in settings:
        Base.metadata.create_all(engine)

    request = application.request_class(
        app=application, environ={'PATH_INFO': '/'})

    transaction.manager.begin()
    context = UserCollection(
        request, application.get_authmanager_storage(request, UserSchema))
    try:
        default_user = settings['authmanager']['default_user']
        default_password = settings['authmanager']['default_password']
        context.create({'username': default_user,
                        'password': default_password,
                        'state': 'active'})
        gstorage = application.get_authmanager_storage(request, GroupSchema)
        group = gstorage.get('__default__')
        group.add_members([default_user])
        group.grant_member_role(default_user, 'administrator')
    except UserExistsError:
        pass
    transaction.manager.commit()
    return application
