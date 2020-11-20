import morpfw
from morpfw.authz.pas import DefaultAuthzPolicy


class App(morpfw.SQLApp, DefaultAuthzPolicy):
    pass


App.hook_auth_models(prefix="/api/v1/auth")
