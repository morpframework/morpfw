import os
import morepath
import yaml
import json
import socket
import time
from multiprocessing import Process
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
        'celery_settings':  {
            'broker_url': 'amqp://guest:guest@localhost:34567/',
            'result_backend': 'db+postgresql://postgres@localhost:45678/morp_tests'
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
    os.environ['MORP_SETTINGS'] = json.dumps(settings)
    c = Client(appobj)
    return c


def start_scheduler(app):
    settings = app._raw_settings
    hostname = socket.gethostname()
    ss = settings['worker']['celery_settings']
    sched = app.celery.Beat(
        hostname='testscheduler.%s' % hostname, **ss)
    proc = Process(target=sched.run)
    proc.daemon = True
    proc.start()
    time.sleep(2)
    return proc


def start_worker(app):
    settings = app._raw_settings
    hostname = socket.gethostname()
    ss = settings['worker']['celery_settings']
    worker = app.celery.Worker(
        hostname='testworker.%s' % hostname, **ss)
    proc = Process(target=worker.start)
    proc.daemon = True
    proc.start()
    time.sleep(2)
    return proc
