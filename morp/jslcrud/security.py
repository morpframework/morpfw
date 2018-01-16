from .app import App
from .model import CRUDCollection, CRUDModel
from . import permission


@App.permission_rule(model=CRUDModel, permission=permission.All)
def model_permissions(identity, model, permission):
    return True


@App.permission_rule(model=CRUDCollection, permission=permission.All)
def collection_permissions(identity, model, permission):
    return True
