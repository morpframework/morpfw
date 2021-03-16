import base64
import functools
import secrets

import morepath
import morpfw
from jwt import InvalidTokenError
from more.jwtauth import JWTIdentityPolicy
from morpfw.authn.base import AuthnPolicy as BaseAuthnPolicy
from morpfw.authn.pas.policy import Identity
from morpfw.crud.util import resolve_model
from oauthlib.common import Request as OAuthRequest
from oauthlib.oauth2 import RequestValidator as BaseRequestValidator
from oauthlib.oauth2 import Server
from oauthlib.oauth2.rfc6749 import errors
from webob.exc import HTTPBadRequest, HTTPForbidden

from .authn.pas.app import App


def jwtpolicy(request: morpfw.Request) -> JWTIdentityPolicy:
    settings = request.app.settings.configuration.__dict__["morpfw.security.jwt"].copy()
    return JWTIdentityPolicy(**settings)


class RequestValidator(BaseRequestValidator):
    def __init__(self, request: morpfw.Request) -> None:
        self.mfw_request = request

        super().__init__()

    def validate_client_id(self, client_id: str, request: OAuthRequest):
        clients = self.mfw_request.get_collection("morpfw.pas.apikey")
        if clients.get_by_identity(client_id):
            return True
        return False

    def authenticate_client(self, request, *args, **kwargs):
        clients = self.mfw_request.get_collection("morpfw.pas.apikey")
        client = None
        if request._params["refresh_token"]:
            jwt = jwtpolicy(self.mfw_request)
            tokendata = jwt.decode_jwt(request._params["refresh_token"])
            client = clients.get_by_identity(tokendata["client_id"])
            request.client = client
        else:
            auth_method, auth_token = request.headers["Authorization"].split(" ")
            client_id, client_secret = (
                base64.b64decode(auth_token.encode("utf-8")).decode("utf-8").split(":")
            )
            client = clients.get_by_identity(client_id)
            if client.validate(client_secret):
                request.client = client
        if client is not None:
            return True
        return False

    def validate_grant_type(
        self, client_id, grant_type, client, request, *args, **kwargs
    ):
        if grant_type in ["client_credentials", "authorization_code", "refresh_token"]:
            return True
        return False

    def get_default_scopes(self, client_id, request, *args, **kwargs):
        return ["home", "admin"]

    def validate_scopes(self, client_id, scopes, client, request, *args, **kwargs):
        return True

    def save_bearer_token(self, token, request, *args, **kwargs):
        return self.mfw_request.relative_url("/")

    #    def validate_code(self, client_id, code, client, request, *args, **kwargs):
    #        # FIXME
    #        return True
    #
    #    def validate_refresh_token(self, refresh_token, client, request, *args, **kwargs):
    #        jwt = jwtpolicy(self.mfw_request)
    #        try:
    #            tokendata = jwt.decode_jwt(request._params["refresh_token"])
    #        except InvalidTokenError:
    #            return False
    #        return True
    #
    #    def get_original_scopes(self, refresh_token, request, *args, **kwargs):
    #        return self.get_default_scopes(request.client.client_id, request)
    #
    #    def revoke_token(self, token, token_type_hint, request, *args, **kwargs):
    #        jwt = jwtpolicy(self.mfw_request)
    #        data = jwt.decode_jwt(token, False)
    #        users = self.mfw_request.get_collection("morpfw.pas.user")
    #        user = users.get_by_userid(data["userid"])
    #        if user:
    #            user.update({"nonce": secrets.token_hex(8)})
    #        return
    #
    #    def save_authorization_code(self, client_id, code, request, *args, **kwargs):
    #        # FIXME
    #        return
    #
    #    def validate_redirect_uri(self, client_id, redirect_uri, request, *args, **kwargs):
    #        # FIXME
    #        return True
    #
    #    def confirm_redirect_uri(
    #        self, client_id, code, redirect_uri, client, request, *args, **kwargs
    #    ):
    #        # FIXME
    #        return True
    #
    #    def invalidate_authorization_code(self, client_id, code, request, *args, **kwargs):
    #        # FIXME
    #        return
    #
    #
    #    def validate_response_type(
    #        self, client_id, response_type, client, request, *args, **kwargs
    #    ):
    #        if response_type in ["code"]:
    #            return True
    #        return False

    def generate_access_token(self, request):
        jwt = jwtpolicy(self.mfw_request)
        user = request.client.user()
        identity = Identity(
            self.mfw_request, user.userid, client_id=request.client.client_id
        )
        claims = identity.as_dict()
        userid = claims.pop("userid")
        claims_set = jwt.create_claims_set(self.mfw_request, userid, claims)
        token = jwt.encode_jwt(claims_set)
        return token

    def get_default_redirect_uri(self, client_id, request, *args, **kwargs):
        return self.mfw_request.relative_url("/")


def oauthserver(request: morpfw.Request) -> Server:
    validator = RequestValidator(request)
    return Server(
        validator,
        token_generator=validator.generate_access_token,
        refresh_token_generator=validator.generate_access_token,
    )


class OAuthRoot(object):
    def __init__(self, request) -> None:
        self.request = request


def extract_params(request: morepath.Request):
    uri = request.url
    http_method = request.method
    body = request.body
    headers = dict(request.headers)
    return uri, http_method, body, headers


class OAuthProvider(object):
    def __init__(self, context, request) -> None:
        self.context = context
        self.request = request
        self.server = oauthserver(request)

    def authorization_form(self):
        request = self.request
        uri, http_method, body, headers = extract_params(request)

        try:
            (scopes, credentials,) = self.server.validate_authorization_request(
                uri, http_method, body, headers
            )
            # Not necessarily in session but they need to be
            # accessible in the POST view after form submit.
            request.session["oauth2_credentials"] = credentials
            request.session.save()
            return self._authorization_form(scopes, credentials)

        # Errors that should be shown to the user on the provider website
        except errors.FatalClientError as e:
            return self.response_from_error(e)

        # Errors embedded in the redirect URI back to the client
        except errors.OAuth2Error as e:
            return morepath.redirect(e.in_uri(e.redirect_uri))

    def _authorization_form(self, scopes, credentials):
        credentials = credentials.copy()
        del credentials["request"]
        return {
            "scopes": scopes,
            "credentials": credentials,
            "submit_url": "/authorize",
        }

    def authorize(self):
        request = self.request
        uri, http_method, body, headers = extract_params(request)

        # The scopes the user actually authorized, i.e. checkboxes
        # that were selected.
        scopes = request.POST.getall("scopes")

        # Extra credentials we need in the validator
        # tem
        credentials = {"user": request.identity.userid}

        # The previously stored (in authorization GET view) credentials
        credentials.update(request.session.get("oauth2_credentials", {}))
        try:
            headers, body, status = self.server.create_authorization_response(
                uri, http_method, body, headers, scopes, credentials
            )
            return self.response_from_return(headers, body, status)

        except errors.FatalClientError as e:
            return self.response_from_error(e)

    def get_token(self):
        request = self.request
        uri, http_method, body, headers = extract_params(request)
        # If you wish to include request specific extra credentials for
        # use in the validator, do so here.
        credentials = {}

        headers, body, status = self.server.create_token_response(
            uri, http_method, body, headers, credentials
        )

        # All requests to /token will return a json response, no redirection.
        return self.response_from_return(headers, body, status)

    def refresh_token(self):
        request = self.request
        uri, http_method, body, headers = extract_params(request)
        # If you wish to include request specific extra credentials for
        # use in the validator, do so here.
        credentials = {}

        headers, body, status = self.server.create_revocation_response(
            uri, http_method, body, headers
        )

        # All requests to /token will return a json response, no redirection.
        return self.response_from_return(headers, body, status)

    def response_from_return(self, headers, body, status):
        return morepath.Response(body=body, headers=headers, status=status)

    def response_from_error(self, e):
        raise HTTPBadRequest()


# @App.json(model=OAuthRoot, name="authorize")
# def authorize(context, request):
#    oauth = OAuthProvider(context, request)
#    res = oauth.authorization_form()
#    return res
#
#
# @App.json(model=OAuthRoot, name="authorize", request_method="POST")
# def authorize(context, request):
#    oauth = OAuthProvider(context, request)
#    res = oauth.authorize()
#    return res
#


@App.json(model=OAuthRoot, name="token", request_method="POST")
def get_token(context, request):
    oauth = OAuthProvider(context, request)
    res = oauth.get_token()
    return res


class AuthnPolicy(BaseAuthnPolicy):
    def get_identity_policy(self, settings):
        jwtauth_settings = settings.configuration.__dict__["morpfw.security.jwt"]
        jwtauth_settings["auth_header_prefix"] = "Bearer"
        if jwtauth_settings:
            # Pass the settings dictionary to the identity policy.
            return JWTIdentityPolicy(**jwtauth_settings)
        raise Exception("JWTAuth configuration is not set")

    def verify_identity(self, app, identity):
        return True


def hook_oauth_models(cls, path="/oauth2"):
    @cls.path(model=OAuthRoot, path=path)
    def get_authroot(request):
        return OAuthRoot(request)


App.hook_oauth_models = classmethod(hook_oauth_models)
