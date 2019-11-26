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
from morpfw import cli
from morpfw.authn.pas.exc import UserExistsError


def get_client(app, config='settings.yml', **kwargs):
    configpath = os.path.join(os.path.dirname(__file__), config)
    settings = cli.load_settings(configpath)
    appobj = create_app(app, settings, **kwargs)
    appobj.initdb()
    c = Client(appobj)
    return c


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
