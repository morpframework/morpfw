from .model import GroupModel, GroupCollection, GroupSchema


def get_group(request, identifier):
    storage = request.app.get_authmanager_storage(request, GroupSchema)
    return storage.get(identifier)


def get_group_collection(request):
    return GroupCollection(request,
                           request.app.get_authmanager_storage(request, GroupSchema))
