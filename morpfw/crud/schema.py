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


@App.identifierfields(schema=Schema)
def identifierfields(schema):
    return ['uuid']

@App.default_identifier(schema=Schema)
def default_identifier(schema, obj, request):
    fields = request.app.get_identifierfields(schema)
    res = []
    for f in fields:
        if f == 'uuid':
            res.append(uuid4().hex)
        else:
            res.append(obj[f])
    return res


