from .model import GroupModel, GroupCollection, GroupSchema


def group_model_factory(app, request, identifier):
    storage = app.get_authmanager_storage(request, GroupSchema)
    return storage.get(identifier)


def group_collection_factory(app, request):
    return GroupCollection(request,
                           app.get_authmanager_storage(request, GroupSchema))
