import morpfw
from morpfw.authz.pas import DefaultAuthzPolicy
from morpfw.crud import permission as crudperm
from morpfw.permission import All


class AppRoot(object):
    def __init__(self, request):
        self.request = request


class App(DefaultAuthzPolicy, morpfw.SQLApp):
    pass


@App.path(model=AppRoot, path="/")
def get_approot(request):
    return AppRoot(request)


@App.permission_rule(model=AppRoot, permission=All)
def allow_all(identity, context, permission):
    """ Default permission rule, allow all """
    return True


@App.json(model=AppRoot)
def index(context, request):
    return {"message": "Hello World"}
