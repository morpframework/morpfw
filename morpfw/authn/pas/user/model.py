import morepath
from morpfw.crud import Collection, Model, StateMachine
from morpfw.crud import errors as cruderrors
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
from ..group.model import GroupCollection, GroupSchema, GroupModel
from uuid import uuid4
import re
import jsonobject
from .schema import RegistrationSchema, UserSchema, LoginSchema
from ..exc import UserExistsError
from ..utils import has_role


class UserCollection(Collection):
    schema = UserSchema
    exist_exc = UserExistsError

    def authenticate(self, username, password):
        if re.match(EMAIL_PATTERN, username):
            user = self.storage.get_by_email(username)
        else:
            user = self.storage.get(username)

        if user is None:
            return None
        if not user.validate(password):
            return None
        return user

    def get_by_userid(self, userid):
        return self.storage.get_by_userid(userid)

    def _create(self, data):
        return super(UserCollection, self)._create(data)


class UserModel(Model):

    schema = UserSchema

    blob_fields = ['profile-photo']

    @property
    def userid(self):
        return self.storage.get_userid(self)

    @property
    def identity(self):
        return morepath.Identity(self.userid)

    def change_password(self, password, new_password):
        if not has_role(self.request, 'administrator'):
            if not self.validate(password, check_state=False):
                raise exc.InvalidPasswordError(self.userid)
        self.storage.change_password(self.identity.userid, new_password)

    def validate(self, password, check_state=True):
        if check_state and self.data['state'] != 'active':
            return False
        return self.storage.validate(self.userid, password)

    def groups(self):
        return self.storage.get_user_groups(self.userid)

    def group_roles(self):
        group_roles = {}
        for g in self.groups():
            group_roles[g.data['groupname']] = g.get_member_roles(
                self.userid)
        return group_roles

    def _links(self):
        links = super()._links()
        links.append({
            'rel': 'userid',
            'value': self.userid
        })
        for g in self.groups():
            links.append({
                'rel': 'group',
                'name': g.identifier,
                'href': self.request.link(g),
            })
        return links


class UserStateMachine(StateMachine):

    states = ['active', 'inactive', 'deleted']
    transitions = [
        {'trigger': 'activate', 'source': 'inactive', 'dest': 'active'},
        {'trigger': 'deactivate', 'source': 'active', 'dest': 'inactive'},
    ]


@App.statemachine(model=UserModel)
def userstatemachine(context):
    return UserStateMachine(context)


class UserRulesAdapter(Adapter):

    def transform_json(self, data):
        data = data.copy()
        for f in ['password', 'password_validate']:
            if f in data.keys():
                del data[f]
        return data


@App.rulesadapter(model=UserModel)
def get_rulesadapter(obj):
    return UserRulesAdapter(obj)


@App.subscribe(signal=crudsignal.OBJECT_CREATED, model=UserModel)
def add_user_to_default_group(app, request, obj, signal):
    request = obj.request
    storage = app.get_storage(GroupModel, request)
    g = storage.get('__default__')
    if g is None:
        gcol = GroupCollection(request, storage)
        g = gcol.create({'groupname': '__default__'})
    g.add_members([obj.userid])
