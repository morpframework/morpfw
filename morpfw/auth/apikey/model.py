from morpfw.crud import Schema, Collection, Model
from .schema import APIKeySchema
import jsl
from ..app import App
from uuid import uuid4
import rulez


class APIKeyModel(Model):
    schema = APIKeySchema


class APIKeyCollection(Collection):
    schema = APIKeySchema

    def search(self, query=None, *args, **kwargs):
        if kwargs.get('secure', True):
            if query:
                rulez.and_(
                    rulez.field['userid'] == self.request.identity.userid,
                    query)
            else:
                query = rulez.field['userid'] == self.request.identity.userid
        return super(APIKeyCollection, self).search(query, *args, **kwargs)
