from ...app import BaseApp as App
from ...crud import permission as crudperms
from ...crud.model import Collection, Model
from ...permission import All


@App.authz_rule(name="morpfw.transit-edit")
def group_policy(groupname, identity, model, permission):
    request = model.request
    users = request.get_collection("morpfw.pas.user")
    user = users.get_by_userid(identity.userid)
    if user["is_administrator"]:
        return True

    if groupname not in [g["groupname"] for g in user.groups()]:
        return False

    if isinstance(model, Collection):
        if issubclass(permission, crudperms.View):
            return True
        if issubclass(permission, crudperms.Search):
            return True

    elif isinstance(model, Model):
        if issubclass(permission, crudperms.View):
            return True

        if issubclass(permission, crudperms.Edit):
            return True

        if issubclass(permission, crudperms.StateUpdate):
            return True
    return False

