from .app import App
from .user.model import UserModel
from . import permission as authperm
from ..crud import permission as crudperm


@App.permission_rule(model=UserModel, permission=authperm.ChangePassword)
def allow_change_password(identity, context, permission):
    return True


@App.permission_rule(model=UserModel, permission=crudperm.Delete)
def allow_delete_user(identity, context, permission):
    if context.request.app.has_role(context.request, 'administrator'):
        return True
    if context['id'] == identity.userid:
        return True
    return False
