from ...app import BaseApp as App
from ...crud import permission as crudperms
from ...crud.model import Collection, Model
from ...permission import All


@App.authz_rule(name="morpfw.fullaccess")
def group_policy(groupname, identity, model, permission):
    request = model.request
    users = request.get_collection("morpfw.pas.user")
    user = users.get_by_userid(identity.userid)
    if user["is_administrator"]:
        return True

    if groupname not in [g["groupname"] for g in user.groups()]:
        return False

    if issubclass(permission, All):
        return True

    return False

