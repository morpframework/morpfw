import jsonobject
from morpfw.crud import Schema
from morpfw.crud.validator import regex_validator
from ..model import NAME_PATTERN, EMAIL_PATTERN
from ..app import App
from dataclasses import dataclass, field
import typing


@dataclass
class RegistrationSchema(object):
    # pattern=NAME_PATTERN)
    username: typing.Optional[str] = field(default=None, metadata={
        'morpfw': {
            'required': True,
            'validators': [regex_validator(NAME_PATTERN, 'name')]
        }
    })

    email: typing.Optional[str] = field(default=None, metadata={
        'morpfw': {
            'required': True,
            'validators': [regex_validator(EMAIL_PATTERN, 'email')]
        }
    })

    password: typing.Optional[str] = field(default=None, metadata={
        'morpfw': {'required': True}})
    password_validate: typing.Optional[str] = field(default=None, metadata={
        'morpfw': {'required': True}})


@dataclass
class LoginSchema(object):
    username: typing.Optional[str] = field(default=None, metadata={
        'morpfw': {'required': True}})

    password: typing.Optional[str] = field(default=None, metadata={
        'morpfw': {'required': True}})


@dataclass
class UserSchema(Schema):

    username: typing.Optional[str] = field(default=None, metadata={
        'morpfw': {
            'required': True,
            'validators': [regex_validator(NAME_PATTERN, 'name')]
        }
    })

    email: typing.Optional[str] = field(default=None, metadata={
        'morpfw': {
            'required': True,
            'validators': [regex_validator(EMAIL_PATTERN, 'email')]
        }
    })

    password: typing.Optional[str] = field(default=None)
    source: typing.Optional[str] = field(default='local')


@App.identifierfields(schema=UserSchema)
def user_identifierfields(schema):
    return ['username']
