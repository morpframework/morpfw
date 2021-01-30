import importlib

from .authn.pas import permission as authperm
from .authn.pas.apikey.model import APIKeyCollection, APIKeyModel
from .authn.pas.user.model import CurrentUserModel, UserCollection, UserModel
from .authz.pas import DefaultAuthzPolicy
from .crud import permission as crudperms
from .crud.model import Collection, Model
from .permission import All

Policy = DefaultAuthzPolicy


def import_name(name):
    modname, objname = name.split(":")
    mod = importlib.import_module(modname)
    return getattr(mod, objname)


def eval_config_groupperms(request, model, permission, identity):
    usercol = request.get_collection("morpfw.pas.user")
    user = usercol.get_by_userid(identity.userid)
    if user["is_administrator"]:
        return True

    if isinstance(model, (Collection, Model)):
        config = request.app.get_config("morpfw.authz.type_permissions", {})
        typeinfo = request.app.get_typeinfo_by_schema(model.schema, request)
        type_conf = config.get(typeinfo["name"], {})
        for g in user.groups():
            rule_name = type_conf.get(g["groupname"], None)
            if rule_name:
                rule_func = request.app.get_authz_rule(rule_name)
                if rule_func(g["groupname"], identity, model, permission):
                    return True

    config = request.app.get_config("morpfw.authz.model_permissions", {})

    model_conf = None
    for model_name in config.keys():
        model_klass = import_name(model_name)
        if isinstance(model, model_klass):
            model_conf = config[model_name]
            break

    if not model_conf:
        return

    for g in user.groups():
        rule_name = model_conf.get(g["groupname"], None)
        if rule_name:
            rule_func = request.app.get_authz_rule(rule_name)
            if rule_func(g["groupname"], identity, model, permission):
                return True

    return None


def currentuser_permission(identity, model, permission):
    request = model.request
    usercol = request.get_collection("morpfw.pas.user")
    user = usercol.get_by_userid(identity.userid)
    if user["is_administrator"]:
        return True
    userid = identity.userid
    if isinstance(model, UserModel):
        if model.userid == userid:
            return True
    elif isinstance(model, APIKeyModel):
        if model["userid"] == userid:
            return True

    return False


@Policy.permission_rule(model=UserCollection, permission=authperm.Register)
def allow_api_registration(identity, model, permission):
    return model.request.app.get_config("morpfw.new_registration.enabled", True)


@Policy.permission_rule(model=UserModel, permission=crudperms.All)
def allow_user_crud(identity, model, permission):
    return currentuser_permission(identity, model, permission)


@Policy.permission_rule(model=UserModel, permission=authperm.ChangePassword)
def allow_change_all_user_password(identity, model, permission):
    request = model.request
    usercol = request.get_collection("morpfw.pas.user")
    user = usercol.get_by_userid(identity.userid)
    if user["is_administrator"]:
        return True
    return False


@Policy.permission_rule(model=CurrentUserModel, permission=authperm.ChangePassword)
def allow_change_self_password(identity, model, permission):
    return currentuser_permission(identity, model, permission)


@Policy.permission_rule(model=APIKeyCollection, permission=crudperms.All)
def allow_apikeycollection_management(identity, model, permission):
    request = model.request
    usercol = request.get_collection("morpfw.pas.user")
    user = usercol.get_by_userid(identity.userid)
    if user:
        return True
    return False


@Policy.permission_rule(model=APIKeyModel, permission=crudperms.All)
def allow_apikey_management(identity, model, permission):
    return currentuser_permission(identity, model, permission)


@Policy.permission_rule(model=Collection, permission=All)
def collection_permission(identity, model, permission):
    return eval_config_groupperms(model.request, model, permission, identity)


@Policy.permission_rule(model=Model, permission=All)
def model_permission(identity, model, permission):
    return eval_config_groupperms(model.request, model, permission, identity)

