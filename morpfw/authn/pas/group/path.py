from .model import GroupModel, GroupCollection, GroupSchema
import morepath
from ..app import App


def get_group(request: morepath.Request, identifier: str) -> GroupModel:
    collection = get_group_collection(request)
    return collection.get(identifier)


def get_group_collection(request: morepath.Request) -> GroupCollection:
    storage = request.app.get_storage(GroupModel, request)
    return GroupCollection(request, storage)
