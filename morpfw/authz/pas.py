import morepath

from ..authn.pas import permission as authperm
from ..authn.pas.apikey.model import APIKeyCollection, APIKeyModel
from ..authn.pas.group.model import GroupCollection, GroupModel
from ..authn.pas.group.path import get_group_collection
from ..authn.pas.group.schema import GroupSchema
from ..authn.pas.user.model import CurrentUserModel, UserCollection, UserModel
from ..authn.pas.utils import has_role
from ..crud import permission as crudperm
from ..crud.model import Collection, Model


class DefaultAuthzPolicy(morepath.App):
    pass


def _has_admin_role(context):
    return has_role(context.request, "administrator")


@DefaultAuthzPolicy.permission_rule(model=Model, permission=crudperm.All)
def reject_all_model_access(identity, context, permission):
    return False


@DefaultAuthzPolicy.permission_rule(model=Collection, permission=crudperm.All)
def reject_all_collection_access(identity, context, permission):
    return False


@DefaultAuthzPolicy.permission_rule(model=UserCollection, permission=authperm.Register)
def allow_register(identity, context, permission):
    if _has_admin_role(context):
        return True
    return False


@DefaultAuthzPolicy.permission_rule(model=UserCollection, permission=crudperm.All)
def allow_users_management(identity, context, permission):
    if _has_admin_role(context):
        return True
    return False


@DefaultAuthzPolicy.permission_rule(model=UserModel, permission=crudperm.StateUpdate)
def allow_users_state_management(identity, context, permission):
    if _has_admin_role(context):
        return True
    return False


@DefaultAuthzPolicy.permission_rule(model=GroupCollection, permission=crudperm.All)
def allow_groups_management(identity, context, permission):
    if _has_admin_role(context):
        return True
    return False


@DefaultAuthzPolicy.permission_rule(model=GroupModel, permission=crudperm.All)
def allow_group_management(identity, context, permission):
    if _has_admin_role(context):
        return True
    return False


@DefaultAuthzPolicy.permission_rule(model=UserModel, permission=crudperm.All)
def allow_user_management(identity, context, permission):
    if _has_admin_role(context):
        return True
    if context["uuid"] == identity.userid:
        return True
    return False


@DefaultAuthzPolicy.permission_rule(model=UserModel, permission=authperm.ChangePassword)
def allow_change_password(identity, context, permission):
    if _has_admin_role(context):
        return True
    return False


@DefaultAuthzPolicy.permission_rule(
    model=CurrentUserModel, permission=authperm.ChangePassword
)
def allow_self_change_password(identity, context, permission):
    if context["uuid"] == identity.userid:
        return True
    return False


@DefaultAuthzPolicy.permission_rule(model=APIKeyCollection, permission=crudperm.All)
def allow_apikeys_management(identity, context, permission):
    return True


@DefaultAuthzPolicy.permission_rule(model=APIKeyModel, permission=crudperm.All)
def allow_apikey_management(identity, context, permission):
    if _has_admin_role(context):
        return True
    if context["userid"] == identity.userid:
        return True
    return False
