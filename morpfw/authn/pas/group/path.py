from .model import GroupModel, GroupCollection, GroupSchema
import morepath
from ..app import App


def get_group(request: morepath.Request, identifier: str) -> GroupModel:
    collection = get_group_collection(request)
    return collection.get(identifier)


def get_group_collection(request: morepath.Request) -> GroupCollection:
    authnzprovider = request.app.get_authn_provider(request)
    storage = authnzprovider.get_storage(GroupModel, request)
    return GroupCollection(request, storage)


@App.path(model=GroupModel,
          path='group/{identifier}')
def _get_group(app, request, identifier):
    return get_group(request, identifier)


@App.path(model=GroupCollection,
          path='group')
def _get_group_collection(app, request):
    return get_group_collection(request)
