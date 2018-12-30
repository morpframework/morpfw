import jsonobject
from morpfw.crud import Schema


class APIKeySchema(Schema):

    userid = jsonobject.StringProperty()
    label = jsonobject.StringProperty()
    api_identity = jsonobject.StringProperty()
    api_secret = jsonobject.StringProperty()
