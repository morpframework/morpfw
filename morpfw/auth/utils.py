from .group.path import get_group_collection


def rellink(context, request, name=None, method='GET', link_name=None):
    link_name = link_name or name
    if name:
        name = '+%s' % name
    if name is None:
        link_name = 'self'
    return {
        'rel': link_name,
        'type': method,
        'href': request.link(context, name)
    }


def has_role(request, role, userid=None, groupname='__default__'):
    group_col = get_group_collection(request)
    defgroup = group_col.get(groupname)
    if not userid:
        userid = request.identity.userid
    roles = defgroup.get_member_roles(userid)
    return role in roles
