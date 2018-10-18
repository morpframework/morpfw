from ...jslcrud import Schema, Collection, Model
import jsl
from ..app import App
from ..dbmodel.apikey import APIKey
from uuid import uuid4
import rulez
import jsonobject


class APIKeySchema(Schema):

    username = jsonobject.StringProperty()
    label = jsonobject.StringProperty()
    api_identity = jsonobject.StringProperty()
    api_secret = jsonobject.StringProperty()


class APIKeyModel(Model):
    schema = APIKeySchema


class APIKeyCollection(Collection):
    schema = APIKeySchema

    def search(self, query=None, *args, **kwargs):
        if kwargs.get('secure', True):
            if query:
                rulez.and_(
                    rulez.field['username'] == self.request.identity.userid,
                    query)
            else:
                query = rulez.field['username'] == self.request.identity.userid
        return super(APIKeyCollection, self).search(query, *args, **kwargs)
