from .model import GroupCollection, GroupModel
from .schema import GroupSchema
from .path import get_group, get_group_collection
from ..app import App


@App.typeinfo(name='morpfw.pas.group', schema=GroupSchema)
def get_typeinfo(request):
    return {
        'title': 'Group',
        'description': 'Group type',
        'schema': GroupSchema,
        'collection': GroupCollection,
        'collection_factory': get_group_collection,
        'model': GroupModel,
        'model_factory': get_group,
        'internal': True
    }
