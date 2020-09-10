import re

from .group.path import get_group_collection

UUID_REGEX = re.compile(r"^([a-f0-9]){32}$")


def rellink(context, request, name=None, method="GET", link_name=None):
    link_name = link_name or name
    if name:
        name = "+%s" % name
    if name is None:
        link_name = "self"
    return {"rel": link_name, "type": method, "href": request.link(context, name)}


def has_role(request, role, userid=None, groupname="__default__"):
    if groupname == "__default__" and role == "administrator":
        # FIXME: this is a workaround hack with PAS
        # it should check for which authentication plugin being used
        if userid and UUID_REGEX.match(userid):
            users = request.get_collection("morpfw.pas.user")
            user = users.get_by_userid(userid)
            if user and user["is_administrator"]:
                return True
            return False

    group_col = get_group_collection(request)
    defgroup = group_col.get_by_groupname(groupname)
    if not userid:
        userid = request.identity.userid
    roles = defgroup.get_member_roles(userid)
    users = request.get_collection("morpfw.pas.user")
    user = users.get_by_userid(userid)
    return role in roles
