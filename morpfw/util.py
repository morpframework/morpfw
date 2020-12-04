from urllib.parse import urlparse

from .authn.pas.group.model import GroupCollection, GroupSchema
from .authn.pas.path import get_group, get_group_collection
from .authn.pas.path import get_user_collection as get_user_collection


def create_group(request, groupname):
    collection = get_group_collection(request)
    return collection.create({"groupname": groupname})


def delete_group(request, groupname):
    collection = get_group_collection(request)
    group = collection.get_by_groupname(groupname)
    group.delete()


def get_user(request, username):
    collection = get_user_collection(request)
    return collection.get_by_username(username)


def get_user_by_userid(request, userid):
    collection = get_user_collection(request)
    return collection.get_by_userid(userid)


