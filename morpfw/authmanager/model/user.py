from ...jslcrud import Collection, Model, StateMachine
from ...jslcrud import errors as cruderrors
from ..dbmodel.user import User
from ..app import App
import jsl
from .. import exc
import sqlalchemy as sa
import sqlalchemy_jsonfield as sajson
from .base import BaseSchema, NAME_PATTERN, EMAIL_PATTERN
from ...jslcrud import signals as crudsignal
from ...jslcrud import errors as cruderrors
from .group import GroupCollection, GroupSchema
from uuid import uuid4
import re


class RegistrationSchema(jsl.Document):
    class Options(object):
        title = 'credential'

    username = jsl.StringField(required=True, pattern=NAME_PATTERN)
    email = jsl.StringField(required=True, pattern=EMAIL_PATTERN)
    password = jsl.StringField(required=True)
    password_validate = jsl.StringField(required=True)


class LoginSchema(jsl.Document):
    class Options(object):
        title = 'credential'

    username = jsl.StringField(required=True)
    password = jsl.StringField(required=True)


class UserSchema(BaseSchema):
    class Options(object):
        title = 'user'
        additional_properties = True
    username = jsl.StringField(required=True, pattern=NAME_PATTERN)
    email = jsl.StringField(required=True, pattern=EMAIL_PATTERN)
    password = jsl.StringField(required=False)
    groups = jsl.ArrayField(items=jsl.StringField(
        pattern=NAME_PATTERN), required=False)
    attrs = jsl.DictField(required=False)
    state = jsl.StringField(required=False)
    created = jsl.StringField(required=False)
    modified = jsl.StringField(required=False)
    nonce = jsl.StringField(required=False)


@App.jslcrud_identifierfields(schema=UserSchema)
def user_identifierfields(schema):
    return ['username']


class UserCollection(Collection):
    schema = UserSchema

    def authenticate(self, username, password):
        if re.match(EMAIL_PATTERN, username):
            user = self.storage.get_by_email(username)
            if user is None:
                return False
            return user.validate(password)

        user = self.storage.get(username)
        if user is None:
            return False
        return user.validate(password)

    def _create(self, data):
        data['nonce'] = uuid4().hex
        exists = self.storage.get(data['username'])
        if exists:
            raise exc.UserExistsError(data['username'])
        return super(UserCollection, self)._create(data)


class UserModel(Model):

    schema = UserSchema

    def change_password(self, password, new_password):
        if not self.app.authmanager_has_role(self.request, 'administrator'):
            if not self.validate(password, check_state=False):
                raise exc.InvalidPasswordError(self.data['username'])
        self.storage.change_password(self.data['username'], new_password)

    def validate(self, password, check_state=True):
        if check_state and self.data['state'] != 'active':
            return False
        return self.storage.validate(self.data['username'], password)

    def groups(self):
        return self.storage.get_user_groups(self.data['username'])

    def group_roles(self):
        group_roles = {}
        for g in self.groups():
            group_roles[g.data['groupname']] = g.get_member_roles(
                self.data['username'])
        return group_roles


class UserStateMachine(StateMachine):

    states = ['active', 'inactive', 'deleted']
    transitions = [
        {'trigger': 'activate', 'source': 'inactive', 'dest': 'active'},
        {'trigger': 'deactivate', 'source': 'active', 'dest': 'inactive'},
        {'trigger': 'delete', 'source': [
            'active', 'inactive'], 'dest': 'deleted'}
    ]

    def on_enter_deleted(self):
        self._context.delete()


@App.jslcrud_statemachine(model=UserModel)
def userstatemachine(context):
    return UserStateMachine(context)


@App.jslcrud_jsontransfrom(schema=UserSchema)
def jsontransform(request, context, data):
    data = data.copy()
    for f in ['password', 'password_validate']:
        if f in data.keys():
            del data[f]
    data['groups'] = [g.identifier for g in context.groups()]
    return data


@App.jslcrud_subscribe(signal=crudsignal.OBJECT_CREATED, model=UserModel)
def add_user_to_default_group(app, request, obj, signal):
    request = obj.request
    storage = app.get_authmanager_storage(request, GroupSchema)
    g = storage.get('__default__')
    if g is None:
        gcol = GroupCollection(request, storage)
        g = gcol.create({'groupname': '__default__'})
    g.add_members([obj.data['username']])
