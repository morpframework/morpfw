from .model import GroupModel, GroupCollection, GroupSchema


def group_model_factory(request, identifier):
    storage = request.app.get_authmanager_storage(request, GroupSchema)
    return storage.get(identifier)


def group_collection_factory(request):
    return GroupCollection(request,
                           request.app.get_authmanager_storage(request, GroupSchema))
