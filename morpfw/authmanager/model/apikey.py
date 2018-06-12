from ...jslcrud import Schema, Collection, Model
import jsl
from ..app import App
from ..dbmodel.apikey import APIKey
from uuid import uuid4
import rulez


class APIKeySchema(Schema):

    username = jsl.StringField()
    label = jsl.StringField()
    api_identity = jsl.StringField()
    api_secret = jsl.StringField()


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
