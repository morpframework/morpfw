from morpfw.crud import Schema, Collection, Model
from .schema import APIKeySchema
from ..app import App
from uuid import uuid4
import rulez


class APIKeyModel(Model):
    schema = APIKeySchema
    update_view_enabled = False


class APIKeyCollection(Collection):
    schema = APIKeySchema

    def create(self, data, deserialize=True):
        if not data.get('userid', None):
            data['userid'] = self.request.identity.userid
        data['api_identity'] = uuid4().hex
        data['api_secret'] = uuid4().hex
        return super().create(data, deserialize=deserialize)

    def search(self, query=None, *args, **kwargs):
        if kwargs.get('secure', True):
            if query:
                rulez.and_(
                    rulez.field['userid'] == self.request.identity.userid,
                    query)
            else:
                query = rulez.field['userid'] == self.request.identity.userid
        return super(APIKeyCollection, self).search(query, *args, **kwargs)
