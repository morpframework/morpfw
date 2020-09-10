from morpfw.crud import permission
from morpfw.crud.errors import UnprocessableError
from morpfw.crud.validator import get_data, validate_schema
from morpfw.util import get_user
from webob.exc import HTTPForbidden, HTTPInternalServerError, HTTPNotFound

from ..app import App
from ..utils import rellink
from ..validator import validate
from .model import GroupCollection, GroupModel, GroupSchema, MemberSchema


@App.json(model=GroupModel, name="members", permission=permission.View)
def list_members(context, request):
    """Return the list of users in the group."""
    members = context.members()
    return {
        "users": [
            {
                "username": m.data["username"],
                "userid": m.userid,
                "roles": context.get_member_roles(m.userid),
                "links": [rellink(m, request)],
            }
            for m in members
        ]
    }


@App.json(
    model=GroupModel, name="grant", request_method="POST", permission=permission.Edit
)
def grant_member(context, request):
    """Grant member roles in the group."""
    mapping = request.json["mapping"]
    for entry in mapping:
        user = entry["user"]
        roles = entry["roles"]
        username = user.get("username", None)
        userid = user.get("userid", None)
        if userid:
            u = context.get_user_by_userid(userid)
        elif username:
            u = context.get_user_by_username(username)
        else:
            u = None
        if u is None:
            raise UnprocessableError("User %s does not exists" % (userid or username))
        for rolename in roles:
            context.grant_member_role(u.userid, rolename)
    return {"status": "success"}


@App.json(
    model=GroupModel, name="revoke", request_method="POST", permission=permission.Edit
)
def revoke_member(context, request):
    """Revoke member roles in the group."""

    mapping = request.json["mapping"]
    for entry in mapping:
        user = entry["user"]
        roles = entry["roles"]
        username = user.get("username", None)
        userid = user.get("userid", None)
        if userid:
            u = context.get_user_by_userid(userid)
        elif username:
            u = context.get_user_by_username(username)
        else:
            u = None
        if u is None:
            raise UnprocessableError("User %s does not exists" % (userid or username))
        for rolename in roles:
            context.revoke_member_role(u.userid, rolename)
    return {"status": "success"}
