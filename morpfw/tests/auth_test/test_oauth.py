import os

import morpfw
import requests
import webob
import yaml
from morpfw.app import SQLApp
from morpfw.authz.pas import DefaultAuthzPolicy
from morpfw.oauth import OAuthRoot
from morpfw.permission import All
from morpfw.sql import Base
from oauthlib.oauth2 import BackendApplicationClient, WebApplicationClient

from ..common import WebTestOAuth2Session, create_admin, get_client
from .test_auth import _test_authentication, login, logout


class Protected(All):
    pass


class App(SQLApp, DefaultAuthzPolicy):
    pass


App.hook_auth_models()


class AppRoot(object):
    def __init__(self, request) -> None:
        self.request = request


@App.path(model=AppRoot, path="/")
def get_approot(request):
    return AppRoot(request)


@App.permission_rule(model=AppRoot, permission=All)
def oauth_permission_rule(identity, context, permission):
    return True


@App.json(model=AppRoot, request_method="HEAD")
def head(context, request):
    return {"status": "success"}


@App.path(model=OAuthRoot, path="/oauth2")
def get_authroot(request):
    return OAuthRoot(request)


@App.json(model=AppRoot, name="protected-view", permission=Protected)
def get_protected_view(context, request):
    return {"status": "success"}


def test_oauth_sqlstorage(pgsql_db):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    config_file = os.path.join(os.path.dirname(__file__), "test_oauth-settings.yml")

    with open(config_file) as cf:
        settings = yaml.safe_load(cf.read())

    with morpfw.request_factory(settings) as request:
        Base.metadata.create_all(bind=request.db_session.bind)
        create_admin(request, "admin", "password", "admin@localhost.localdomain")

    with morpfw.request_factory(settings) as request:
        users = request.get_collection("morpfw.pas.user")
        user = users.get_by_username("admin")
        apikeys = request.get_collection("morpfw.pas.apikey")
        apikey = apikeys.create({"userid": user.uuid, "name": "test"})
        client_secret = apikey.generate_secret()
        client_id = apikey["api_identity"]

    c = get_client(config_file)

    client = BackendApplicationClient(client_id=client_id)
    oauth = WebTestOAuth2Session(c, client=client)

    token = oauth.fetch_token(
        token_url="/oauth2/token", client_id=client_id, client_secret=client_secret,
    )
    result = oauth.get("/+protected-view")

    # client = WebApplicationClient(client_id=client_id)
    # weboauth = WebTestOAuth2Session(c, client=client)

    # login(c, "admin", "password")
    # auth_url, state = weboauth.authorization_url("/oauth2/authorize")
    # r = c.get(auth_url)
    # r = c.post(auth_url, {"scopes": ["home"]})
    # logout(c)
    # token = weboauth.fetch_token(
    #    token_url="/oauth2/token",
    #    client_secret=client_secret,
    #    authorization_response=r.location,
    # )

    # result = weboauth.get("/+protected-view")

    # weboauth.refresh_token("/oauth2/token", refresh_token=token["refresh_token"])
