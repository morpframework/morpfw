from .auth.group.model import GroupSchema, GroupCollection
from .auth.path import group_collection_factory as get_group_collection
from .auth.path import user_collection_factory as get_user_collection


def get_group(request, groupname):
    collection = get_group_collection(request)
    return collection.get(groupname)


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
