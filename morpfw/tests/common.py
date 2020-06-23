import json
import os
import socket
import time
from multiprocessing import Process

import morepath
import transaction
import yaml
from more.basicauth import BasicAuthIdentityPolicy
from more.jwtauth import JWTIdentityPolicy
from morpfw import cli
from morpfw.authn.pas.exc import UserExistsError
from morpfw.main import create_admin as morpfw_create_admin
from morpfw.main import create_app
from morpfw.request import request_factory
from webtest import TestApp as Client


def make_request(appobj):
    request = appobj.request_class(
        environ={
            "PATH_INFO": "/",
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "80",
            "SERVER_PROTOCOL": "HTTP/1.1",
        },
        app=appobj,
    )
    return request


def get_client(config="settings.yml", **kwargs):
    param = cli.load(config)
    request = request_factory(param["settings"], app_factory_opts=kwargs)
    c = Client(request.app)
    c.mfw_request = request
    return c


def create_admin(client: Client, user: str, password: str, email: str):
    appobj = client.app
    morpfw_create_admin(client, user, password, email)
    transaction.commit()


def start_scheduler(app):
    settings = app._raw_settings
    hostname = socket.gethostname()
    ss = settings["configuration"]["morpfw.celery"]
    sched = app.celery.Beat(hostname="testscheduler.%s" % hostname, **ss)
    proc = Process(target=sched.run)
    proc.daemon = True
    proc.start()
    time.sleep(2)
    return proc


def start_worker(app):
    settings = app._raw_settings
    hostname = socket.gethostname()
    ss = settings["configuration"]["morpfw.celery"]
    worker = app.celery.Worker(hostname="testworker.%s" % hostname, **ss)
    proc = Process(target=worker.start)
    proc.daemon = True
    proc.start()
    time.sleep(2)
    return proc
