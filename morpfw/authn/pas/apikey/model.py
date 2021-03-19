import hashlib
import secrets
from uuid import uuid4

import rulez
from morpfw.crud import Collection, Model, Schema

from ..app import App
from .schema import APIKeySchema


class APIKeyModel(Model):
    schema = APIKeySchema
    update_view_enabled = False

    @property
    def client_id(self):
        return self["api_identity"]

    def generate_secret(self):
        api_secret = secrets.token_urlsafe(32)
        pwhash = hashlib.sha256(api_secret.encode("utf-8")).hexdigest()
        self.update({"api_secret": pwhash})
        return api_secret

    def validate(self, api_secret):
        pwhash = hashlib.sha256(api_secret.encode("utf-8")).hexdigest()
        if pwhash == self["api_secret"]:
            return True
        return False

    def user(self):
        users = self.request.get_collection("morpfw.pas.user")
        return users.get_by_userid(self["userid"])


class APIKeyCollection(Collection):
    schema = APIKeySchema
    create_view_enabled = False

    def search(self, query=None, *args, **kwargs):
        if kwargs.get("secure", True):
            if query:
                rulez.and_(rulez.field["userid"] == self.request.identity.userid, query)
            else:
                query = rulez.field["userid"] == self.request.identity.userid
        return super(APIKeyCollection, self).search(query, *args, **kwargs)

    def get_by_identity(self, identity):
        res = self.search(rulez.field("api_identity") == identity)
        if res:
            return res[0]
        return None
