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


