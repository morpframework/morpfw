from ..app import App
from ..model.apikey import APIKeyModel, APIKeyCollection
from ..path import user_factory, apikey_collection_factory, apikey_factory
from ...jslcrud import permission
import uuid
import rulez
import morepath


@App.json(model=APIKeyCollection, request_method='POST',
          permission=permission.Create)
def generate_apikey(context, request):
    user = user_factory(request.app, request, request.identity.userid)
    data = {}
    data['username'] = request.identity.userid
    if not user.validate(request.json['password']):
        @request.after
        def adjust_response(response):
            response.status = 422

        return {'status': 'error', 'message': 'Invalid password'}

    data['api_identity'] = uuid.uuid4().hex
    data['api_secret'] = uuid.uuid4().hex
    data['label'] = request.json['label']
    obj = context.create(data)
    return obj.json()
