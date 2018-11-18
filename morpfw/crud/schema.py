import jsonobject
from uuid import uuid4
from .app import App

class Schema(jsonobject.JsonObject):

    uuid = jsonobject.StringProperty(required=False, 
        default=lambda: uuid4().hex)
    creator = jsonobject.StringProperty(required=False)
    created = jsonobject.DateTimeProperty(required=False)
    modified = jsonobject.DateTimeProperty(required=False)
    state = jsonobject.StringProperty(required=False)
    deleted = jsonobject.DateTimeProperty(required=False)


@App.jslcrud_identifierfields(schema=Schema)
def default_identifierfields(schema):
    return ['uuid']

