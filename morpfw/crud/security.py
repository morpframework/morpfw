from .app import App
from .model import Collection, Model
from . import permission


@App.permission_rule(model=Model, permission=permission.All)
def model_permissions(identity, model, permission):
    return True


@App.permission_rule(model=Collection, permission=permission.All)
def collection_permissions(identity, model, permission):
    return True
