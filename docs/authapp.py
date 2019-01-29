from morpfw.authn.pas.policy import SQLStorageAuthApp
from morpfw.authn.pas.policy import SQLStorageAuthnPolicy
from morpfw.authz.pas import DefaultAuthzPolicy
from .app import App


class AuthApp(SQLStorageAuthApp, DefaultAuthzPolicy):
    pass


class AuthnPolicy(SQLStorageAuthnPolicy):
    app_cls = AuthApp


@App.mount(app=AuthnPolicy.app_cls, path='/auth')
def mount_authapp(app):
    return AuthnPolicy.app_cls()
