import os
import morepath
import yaml
from webtest import TestApp as Client
from more.jwtauth import JWTIdentityPolicy
from more.basicauth import BasicAuthIdentityPolicy
from morpfw.main import create_app
from morpfw.main import create_admin
from morpfw.authn.pas.exc import UserExistsError

DEFAULT_SETTINGS = {
    'application': {
        'authn_policy': 'morpfw.authn.noauth:AuthnPolicy',
        'dburi': 'postgresql://postgres@localhost:45678/morp_tests'
    },
    'worker': {
        'enabled': True,
        'celery_name': 'morp_tasks',
        'celery_settings':  {
            'metastore': 'sqlstorage',
            'broker_url': 'amqp://guest:guest@localhost:38567/',
            'result_backend': 'rpc://'
        }
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
#	try:
#		create_admin(appobj, username='defaultuser',
#					 password='password', email='admin@localhost.localdomain')
#	except UserExistsError:
#		pass
    c = Client(appobj)
    return c
