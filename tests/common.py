import os
import morepath
import yaml
from webtest import TestApp as Client
from more.jwtauth import JWTIdentityPolicy
from more.basicauth import BasicAuthIdentityPolicy
from morp.main import create_app
from morp.app import create_admin
from authmanager.exc import UserExistsError

DEFAULT_SETTINGS = {
    'authmanager': {
        'storage': 'memorystorage',
        'default_user': 'defaultuser',
        'default_password': 'password',
    },
    'jwtauth': {
        'master_secret': 'secret',
        'leeway': 10
    },
    'sqlalchemy': {
        'dburi': 'postgresql://postgres@localhost:45678/morp_tests'
    },
    'morp': {
        'use_celery': True,
        'celery_name': 'morp_tasks',
    },
    'celery': {
        'metastore': 'sqlstorage',
        'broker_url': 'amqp://guest:guest@localhost:38567/',
        'result_backend': 'rpc://'
    }
}


def get_settings(config):
    if isinstance(config, str):
        configpath = os.path.join(os.path.dirname(__file__), config)
        if not os.path.exists(configpath):
            return DEFAULT_SETTINGS
        with open(os.path.join(os.path.dirname(__file__), config)) as f:
            settings = yaml.load(f)
    else:
        settings = config
    return settings


def get_client(app, config='settings.yml', **kwargs):
    settings = get_settings(config)
    appobj = create_app(app, settings, **kwargs)
    appobj.initdb()
    try:
        create_admin(appobj, username='defaultuser', password='password')
    except UserExistsError:
        pass
    c = Client(appobj)
    return c
