import re
import secrets
from datetime import datetime
from uuid import uuid4

import morepath
import pytz
import sqlalchemy as sa
import sqlalchemy_jsonfield as sajson
from morpfw.crud import Collection, Model, StateMachine
from morpfw.crud import errors as cruderrors
from morpfw.crud import signals as crudsignal
from morpfw.crud.schema import Schema
from morpfw.crud.validator import regex_validator

from .. import exc
from ..app import App
from ..exc import UserExistsError
from ..group.model import GroupCollection, GroupModel, GroupSchema
from ..group.path import get_group_collection
from ..model import EMAIL_PATTERN, NAME_PATTERN
from ..utils import has_role
from .schema import LoginSchema, RegistrationSchema, UserSchema


class UserCollection(Collection):
    schema = UserSchema
    exist_exc = UserExistsError
    create_view_enabled = False

    def authenticate(self, username, password):
        if re.match(EMAIL_PATTERN, username):
            user = self.storage.get_by_email(self, username)
        else:
            user = self.storage.get_by_username(self, username)

        if user is None:
            return None
        if not user.validate(password):
            return None
        return user

    def get_by_userid(self, userid):
        return self.storage.get_by_userid(self, userid)

    def get_by_email(self, email):
        return self.storage.get_by_email(self, email)

    def get_by_username(self, username):
        return self.storage.get_by_username(self, username)

    def _create(self, data):
        return super(UserCollection, self)._create(data)


class UserModel(Model):

    schema = UserSchema

    blob_fields = ["profile-photo"]

    def title(self):
        return self["username"]

    @property
    def userid(self):
        return self.storage.get_userid(self)

    @property
    def identity(self):
        return morepath.Identity(self.userid)

    def change_password(self, password: str, new_password: str, secure: bool = True):
        rules = self.rulesprovider()
        result = rules.change_password(password, new_password, secure=secure)
        self.update({"nonce": secrets.token_hex(8)}, deserialize=False)
        return result

    def validate(self, password: str, check_state: bool = True):
        rules = self.rulesprovider()
        return rules.validate(password, check_state)

    def groups(self):
        return self.storage.get_user_groups(self.collection, self.userid)

    def group_roles(self):
        group_roles = {}
        for g in self.groups():
            group_roles[g.data["groupname"]] = g.get_member_roles(self.userid)
        return group_roles

    def timezone(self):
        tz = self["timezone"] or "UTC"
        return pytz.timezone(tz).localize(datetime.now()).tzinfo

    def _links(self):
        links = super()._links()
        links.append({"rel": "userid", "value": self.userid})
        for g in self.groups():
            links.append(
                {
                    "rel": "group",
                    "uuid": g.identifier,
                    "name": g.data["groupname"],
                    "href": self.request.link(g),
                }
            )
        return links


class UserStateMachine(StateMachine):

    states = ["active", "inactive", "deleted"]
    transitions = [
        {"trigger": "activate", "source": "inactive", "dest": "active"},
        {"trigger": "deactivate", "source": "active", "dest": "inactive"},
    ]


@App.statemachine(model=UserModel)
def userstatemachine(context):
    return UserStateMachine(context)


@App.subscribe(signal=crudsignal.OBJECT_CREATED, model=UserModel)
def add_user_to_default_group(app, request, obj, signal):
    request = obj.request
    gcol = get_group_collection(request)
    g = gcol.get_by_groupname("__default__")
    if g is None:
        g = gcol.create({"groupname": "__default__"})
    g.add_members([obj.userid])


class CurrentUserModel(UserModel):
    pass
