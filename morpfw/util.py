from .authn.pas.group.model import GroupSchema, GroupCollection
from .authn.pas.path import get_group_collection, get_group
from .authn.pas.path import get_user_collection as get_user_collection


def create_group(request, groupname):
    collection = get_group_collection(request)
    return collection.create({'groupname': groupname})


def delete_group(request, groupname):
    collection = get_group_collection(request)
    group = collection.get(groupname)
    group.delete()


def get_user(request, username):
    collection = get_user_collection(request)
    return collection.get(username)
