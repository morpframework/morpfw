from ..app import App
from ..model.user import UserCollection, UserModel
from ..path import user_collection_factory
from ..model.user import UserSchema, LoginSchema
from ..model.user import RegistrationSchema
import morepath
from ..validator import validate
from ..utils import rellink
from .. import permission
from webob.exc import HTTPNotFound
from more.jwtauth import (
    verify_refresh_request, InvalidTokenError, ExpiredSignatureError
)


@App.json(model=UserCollection, name='register', request_method='POST',
          permission=permission.Register)
def register(context, request):
    """Validate the username and password and create the user."""
    data = request.json
    res = validate(data, RegistrationSchema.get_schema())
    if res:
        @request.after
        def set_error(response):
            response.status = 422
        return {
            'status': 'error',
            'field_errors': [{'message': res[x]} for x in res.keys()]
        }

    if data['password'] != data['password_validate']:
        @request.after
        def adjust_response(response):
            response.status = 422

        return {'status': 'error',
                'message': 'Password confirmation does not match'}

    if 'state' not in data.keys():
        data['state'] = getattr(
            request.app.settings.authmanager, 'default_userstate', 'active')
    obj = context.create(data)
    return {'status': 'success'}


@App.json(model=UserCollection, name='login')
def login(context, request):
    return {
        'schema': LoginSchema.get_schema(),
        'links': [rellink(context, request, 'login', 'POST')]
    }


@App.json(model=UserCollection, name='create', request_method='POST')
def reject_create(context, request):
    raise HTTPNotFound()


@App.json(model=UserCollection, name='login', request_method='POST')
def process_login(context, request):
    """Authenticate username and password and log in user"""
    username = request.json['username']
    password = request.json['password']

    # Do the password validation.
    if not context.authenticate(username, password):
        @request.after
        def adjust_status(response):
            response.status = 401
        return {
            'status': 'error',
            'error': {
                'code': 401,
                'message': 'Invalid Username / Password'
            }
        }

    @request.after
    def remember(response):
        """Remember the identity of the user logged in."""
        # We pass the extra info to the identity object.
        response.headers.add('Access-Control-Expose-Headers', 'Authorization')
        identity = morepath.Identity(username)
        request.app.remember_identity(response, request, identity)

    return {
        'status': 'success'
    }


@App.json(model=UserCollection, name='refresh_token')
def refresh_token(context, request):
    try:
        # Verifies if we're allowed to refresh the token.
        # In this case returns the userid.
        # If not raises exceptions based on InvalidTokenError.
        # If expired this is a ExpiredSignatureError.
        username = verify_refresh_request(request)
    except ExpiredSignatureError:
        @request.after
        def expired_nonce_or_token(response):
            response.status_code = 403
        return {
            'status': 'error',
            'message': 'Your session has expired.'
        }
    except InvalidTokenError as e:
        @request.after
        def invalid_token(response):
            response.status_code = 403
        return {
            'status': 'error',
            'message': 'Could not refresh your token. %s' % str(e)
        }
    else:
        @request.after
        def remember(response):
            # create the identity with the userid and updated user info
            identity = morepath.Identity(username)
            # create the updated token and set it in the response header
            request.app.remember_identity(response, request, identity)

        return {
            'status': 'success',
            'message': 'Token successfully refreshed'
        }


@App.json(model=UserCollection, name='logout')
def logout(context, request):
    """Log out the user."""

    @request.after
    def forget(response):
        request.app.forget_identity(response, request)

    return {
        'status': 'success'
    }


@App.json(model=UserModel, request_method='POST')
def update(context, request):
    error = None
    if 'password' in request.json.keys():
        error = {
            'status': 'error',
            'message': 'Changing password is not allowed through this method'
        }
    elif 'username' in request.json.keys():
        error = {
            'status': 'error',
            'message': 'Changing username is not allowed'
        }

    if error:
        @request.after
        def adjust_status(response):
            response.status = 422

        return error

    context.update(request.json)
    return {'status': 'success'}


@App.json(model=UserModel, name='roles')
def roles(context, request):
    return context.group_roles()


@App.json(model=UserModel, name='change_password', request_method='POST')
def change_password(context, request):
    data = request.json
    error = None
    current_password = data.get('password', '')
    if not request.app.authmanager_has_role(request, 'administrator'):
        if not context.validate(current_password, check_state=False):
            error = 'Invalid password'

    if not error and data['new_password'] != data['new_password_validate']:
        error = 'Password confirmation does not match'

    if error:
        @request.after
        def adjust_status(response):
            response.status = 422
        return {
            'status': 'error',
            'message': error
        }

    context.change_password(current_password, data['new_password'])
    return {'status': 'success'}


@App.json(model=UserModel, request_method='DELETE')
def delete(context, request):
    sm = context.state_machine()
    try:
        sm.delete()
    except AttributeError:
        @request.after
        def adjust_status(response):
            response.status = 404

        return {
            'status': 'error',
            'message': 'User no longer exists'
        }
    return {'status': 'success'}
