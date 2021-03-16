import json
import os
import socket
import time
from multiprocessing import Process

import morepath
import morpfw
import morpfw.tests
import requests
import transaction
import webob
import yaml
from more.basicauth import BasicAuthIdentityPolicy
from more.jwtauth import JWTIdentityPolicy
from morpfw import cli
from morpfw.authn.pas.exc import UserExistsError
from morpfw.main import create_admin as morpfw_create_admin
from morpfw.main import create_app
from morpfw.request import request_factory
from requests_oauthlib import OAuth2Session
from requests_oauthlib.oauth2_session import (
    InsecureTransportError,
    TokenExpiredError,
    TokenUpdated,
    is_secure_transport,
    log,
)
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
    morepath.scan(morpfw)
    request = request_factory(param["settings"], app_factory_opts=kwargs, scan=False)

    c = Client(request.environ["morpfw.wsgi.app"])
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


class WebTestResponse(object):
    def __init__(self, response: webob.Response):
        self.wt_response = response

    @property
    def status_code(self):
        return self.wt_response.status_code

    @property
    def request(self):
        return self.wt_response.request

    @property
    def headers(self):
        return self.wt_response.headers

    @property
    def text(self):
        return self.wt_response.text


class FakeRequest(object):
    def __init__(self):
        self.headers = {}


class WebTestOAuth2Session(OAuth2Session):
    def __init__(self, wt_client, **kwargs):
        self.wt_client = wt_client
        super().__init__(**kwargs)

    def request(
        self,
        method,
        url,
        data=None,
        headers=None,
        auth=None,
        withhold_token=None,
        client_id=None,
        client_secret=None,
        **kwargs
    ):

        """Intercept all requests and add the OAuth 2 token if present."""
        if not is_secure_transport(url):
            raise InsecureTransportError()
        if self.token and not withhold_token:
            log.debug(
                "Invoking %d protected resource request hooks.",
                len(self.compliance_hook["protected_request"]),
            )
            for hook in self.compliance_hook["protected_request"]:
                log.debug("Invoking hook %s.", hook)
                url, headers, data = hook(url, headers, data)

            log.debug("Adding token %s to request.", self.token)
            try:
                url, headers, data = self._client.add_token(
                    url, http_method=method, body=data, headers=headers
                )
            # Attempt to retrieve and save new access token if expired
            except TokenExpiredError:
                if self.auto_refresh_url:
                    log.debug(
                        "Auto refresh is set, attempting to refresh at %s.",
                        self.auto_refresh_url,
                    )

                    # We mustn't pass auth twice.
                    auth = kwargs.pop("auth", None)
                    if client_id and client_secret and (auth is None):
                        log.debug(
                            'Encoding client_id "%s" with client_secret as Basic auth credentials.',
                            client_id,
                        )
                        auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
                    token = self.refresh_token(
                        self.auto_refresh_url, auth=auth, **kwargs
                    )
                    if self.token_updater:
                        log.debug(
                            "Updating token to %s using %s.", token, self.token_updater
                        )
                        self.token_updater(token)
                        url, headers, data = self._client.add_token(
                            url, http_method=method, body=data, headers=headers
                        )
                    else:
                        raise TokenUpdated(token)
                else:
                    raise

        log.debug("Requesting url %s using method %s.", url, method)
        log.debug("Supplying headers %s and data %s", headers, data)
        log.debug("Passing through key word arguments %s.", kwargs)
        if "json" in kwargs:
            f = getattr(self.wt_client, "%s_json" % method.lower())
            data = kwargs["json"]
        else:
            f = getattr(self.wt_client, method.lower())
        if auth:
            fr = FakeRequest()
            auth(fr)
            headers.update(fr.headers)
        resp = f(url, data, headers=headers)
        return WebTestResponse(resp)

