from .model import UserCollection, UserModel
from .schema import UserSchema
from .path import get_user, get_user_collection
from ..app import App


@App.typeinfo(name='morpfw.pas.user',schema=UserSchema)
def get_typeinfo(request):
    return {
        'title': 'User',
        'description': 'User type',
        'schema': UserSchema,
        'collection': UserCollection,
        'collection_factory': get_user_collection,
        'model': UserModel,
        'model_factory': get_user,
        'internal': True
    }
