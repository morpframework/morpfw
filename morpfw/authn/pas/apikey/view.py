import uuid

import morepath
import rulez
from morpfw.crud import permission

from ..app import App
from ..path import get_apikey, get_apikey_collection, get_user, get_user_collection
from .model import APIKeyCollection, APIKeyModel


@App.json(
    model=APIKeyCollection,
    name="generate",
    request_method="POST",
    permission=permission.Create,
)
def generate_apikey(context, request):
    usercol = get_user_collection(request)
    user = usercol.get_by_userid(request.identity.userid)
    data = {}
    if not user.validate(request.json["password"]):

        @request.after
        def adjust_response(response):
            response.status = 422

        return {"status": "error", "message": "Invalid password"}

    data["name"] = request.json["name"]
    obj = context.create(data)
    secret = obj.generate_secret()
    result = obj.json()
    result["data"]["api_secret"] = secret
    return result
