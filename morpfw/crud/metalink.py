from .app import App
from .model import Collection, Model


class MetalinkProvider(object):
    def __init__(self, request):
        self.request = request
        self.app = request.app

    def link(self, obj, **kwargs) -> dict:
        raise NotImplementedError

    def resolve(self, link) -> str:
        raise NotImplementedError


class CollectionMetalinkProvider(MetalinkProvider):
    def link(self, obj, view_name=None, **kwargs) -> dict:
        typeinfo = self.app.get_typeinfo_by_schema(obj.schema, self.request)
        return {
            "type": "morpfw.collection",
            "resource_type": typeinfo["name"],
            "view_name": view_name,
        }

    def resolve(self, link) -> str:
        col = self.request.get_collection(link["resource_type"])
        return self.request.link(col)


class ModelMetalinkProvider(MetalinkProvider):
    def link(self, obj, view_name=None, **kwargs) -> dict:
        typeinfo = self.app.get_typeinfo_by_schema(obj.schema, self.request)
        return {
            "type": "morpfw.model",
            "resource_type": typeinfo["name"],
            "uuid": obj.uuid,
            "view_name": view_name,
        }

    def resolve(self, link) -> str:
        col = self.request.get_collection(link["resource_type"])
        return self.request.link(col.get_by_uuid(link["uuid"]))


@App.metalink(name="morpfw.collection", model=Collection)
def get_collection_metalink(request):
    return CollectionMetalinkProvider(request)


@App.metalink(name="morpfw.model", model=Model)
def get_model_metalink(request):
    return ModelMetalinkProvider(request)

