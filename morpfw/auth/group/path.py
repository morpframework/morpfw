from .model import GroupModel, GroupCollection, GroupSchema
from ..app import App


def get_group(request, identifier):
    storage = request.app.root.get_authnz_provider(
    ).get_authn_storage(request, GroupSchema)
    return storage.get(identifier)


def get_group_collection(request):
    return GroupCollection(request,
                           request.app.root.get_authnz_provider().get_authn_storage(request, GroupSchema))


@App.path(model=GroupModel,
          path='group/{identifier}')
def _get_group(app, request, identifier):
    return get_group(request, identifier)


@App.path(model=GroupCollection,
          path='group')
def _get_group_collection(app, request):
    return get_group_collection(request)
