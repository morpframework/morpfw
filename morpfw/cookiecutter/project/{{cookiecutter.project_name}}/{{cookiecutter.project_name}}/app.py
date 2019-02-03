import morpfw
from morpfw.authz.pas import DefaultAuthzPolicy
from morpfw.crud import permission as crudperm
import sqlalchemy as sa


class AppRoot(object):

    def __init__(self, request):
        self.request = request


class App(DefaultAuthzPolicy, morpfw.SQLApp):
    pass


@App.path(model=AppRoot, path='/')
def get_approot(request):
    return AppRoot(request)


@App.json(model=AppRoot, permission=crudperm.View)
def index(context, request):
    return {
        'message': 'Hello World'
    }

@App.permission_rule(model=AppRoot, permission=crudperm.View)
def allow_view(identity, context, permission):
    return True
