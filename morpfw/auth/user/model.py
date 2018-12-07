from morpfw.crud import Collection, Model, StateMachine
from morpfw.crud import errors as cruderrors
from .storage import User
from ..app import App
import jsl
from .. import exc
import sqlalchemy as sa
import sqlalchemy_jsonfield as sajson
from ..model import NAME_PATTERN, EMAIL_PATTERN
from morpfw.crud import signals as crudsignal
from morpfw.crud import errors as cruderrors
from morpfw.crud.schema import Schema
from morpfw.crud.rulesadapter import Adapter
from morpfw.crud.validator import regex_validator
from ..group.model import GroupCollection, GroupSchema
from uuid import uuid4
import re
import jsonobject
from .schema import RegistrationSchema, UserSchema, LoginSchema
from ..exc import UserExistsError


class UserCollection(Collection):
    schema = UserSchema
    exist_exc = UserExistsError

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
        return super(UserCollection, self)._create(data)


class UserModel(Model):

    schema = UserSchema

    def change_password(self, password, new_password):
        if not self.app.has_role(self.request, 'administrator'):
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


@App.statemachine(model=UserModel)
def userstatemachine(context):
    return UserStateMachine(context)


class UserRulesAdapter(Adapter):

    def transform_json(self, data):
        data = data.copy()
        for f in ['password', 'password_validate']:
            if f in data.keys():
                del data[f]
        data['groups'] = [g.identifier for g in self.context.groups()]
        return data


@App.rulesadapter(model=UserModel)
def get_rulesadapter(obj):
    return UserRulesAdapter(obj)


@App.subscribe(signal=crudsignal.OBJECT_CREATED, model=UserModel)
def add_user_to_default_group(app, request, obj, signal):
    request = obj.request
    storage = app.get_authn_storage(request, GroupSchema)
    g = storage.get('__default__')
    if g is None:
        gcol = GroupCollection(request, storage)
        g = gcol.create({'groupname': '__default__'})
    g.add_members([obj.data['username']])
