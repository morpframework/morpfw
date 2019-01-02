from .model import GroupModel, GroupCollection, GroupSchema
from ..app import App


def get_group(request, identifier):
    collection = get_group_collection(request)
    return collection.get(identifier)


def get_group_collection(request):
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
