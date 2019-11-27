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
from morpfw.main import create_admin as morpfw_create_admin
from morpfw import cli
from morpfw.authn.pas.exc import UserExistsError
import transaction


def get_client(config='settings.yml', **kwargs):
    param = cli.load(config)
    appobj = param['factory'](param['settings'], **kwargs)
    if hasattr(appobj, 'initdb'):
        appobj.initdb()
    c = Client(appobj)
    return c


def create_admin(client: Client, user: str, password: str, email: str):
    appobj = client.app
    morpfw_create_admin(appobj, user, password, email)
    transaction.commit()


def start_scheduler(app):
    settings = app._raw_settings
    hostname = socket.gethostname()
    ss = settings['configuration']['morpfw.celery']
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
    ss = settings['configuration']['morpfw.celery']
    worker = app.celery.Worker(
        hostname='testworker.%s' % hostname, **ss)
    proc = Process(target=worker.start)
    proc.daemon = True
    proc.start()
    time.sleep(2)
    return proc
