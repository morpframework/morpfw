import jsonobject
from morpfw.crud import Schema
from morpfw.crud.validator import regex_validator
from ..model import NAME_PATTERN, EMAIL_PATTERN
from ..app import App


class RegistrationSchema(jsonobject.JsonObject):
    # pattern=NAME_PATTERN)
    username = jsonobject.StringProperty(
        required=True, validators=[regex_validator(NAME_PATTERN, 'name')])
    # pattern=EMAIL_PATTERN
    email = jsonobject.StringProperty(required=True, validators=[
                                      regex_validator(EMAIL_PATTERN, 'email')])
    password = jsonobject.StringProperty(required=True)
    password_validate = jsonobject.StringProperty(required=True, default='')


class LoginSchema(jsonobject.JsonObject):

    username = jsonobject.StringProperty(required=True)
    password = jsonobject.StringProperty(required=True)


class UserSchema(Schema):

    username = jsonobject.StringProperty(
        required=True, validators=[regex_validator(NAME_PATTERN, 'name')])  # , pattern=NAME_PATTERN)
    # , pattern=EMAIL_PATTERN)
    email = jsonobject.StringProperty(required=True, validators=[
                                      regex_validator(EMAIL_PATTERN, 'email')])
    password = jsonobject.StringProperty(required=False)
    groups = jsonobject.ListProperty(
        str, required=False)  # pattern=NAME_PATTERN
    attrs = jsonobject.DictProperty(required=False)
    state = jsonobject.StringProperty(required=False)
    created = jsonobject.StringProperty(required=False)
    modified = jsonobject.StringProperty(required=False)
    nonce = jsonobject.StringProperty(required=False)


@App.identifierfields(schema=UserSchema)
def user_identifierfields(schema):
    return ['username']
