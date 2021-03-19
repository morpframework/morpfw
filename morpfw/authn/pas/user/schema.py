import secrets
import typing
from dataclasses import dataclass, field

import deform.widget
import pytz
from morpfw.crud.schema import BaseSchema, Schema
from morpfw.crud.validator import regex_validator

from ..app import App
from ..model import EMAIL_PATTERN, NAME_PATTERN
from .validator import valid_source, valid_tz


@dataclass
class RegistrationSchema(BaseSchema):
    # pattern=NAME_PATTERN)
    username: typing.Optional[str] = field(
        default=None,
        metadata={
            "required": True,
            "validators": [regex_validator(NAME_PATTERN, "name")],
        },
    )

    email: typing.Optional[str] = field(
        default=None,
        metadata={
            "required": True,
            "validators": [regex_validator(EMAIL_PATTERN, "email")],
        },
    )

    password: typing.Optional[str] = field(default=None, metadata={"required": True})
    password_validate: typing.Optional[str] = field(
        default=None, metadata={"required": True}
    )


@dataclass
class LoginSchema(BaseSchema):
    username: typing.Optional[str] = field(default=None, metadata={"required": True})

    password: typing.Optional[str] = field(default=None, metadata={"required": True})


@dataclass
class UserSchema(Schema):

    username: typing.Optional[str] = field(
        default=None,
        metadata={
            "required": True,
            "editable": False,
            "searchable": True,
            "validators": [regex_validator(NAME_PATTERN, "name")],
        },
    )

    email: typing.Optional[str] = field(
        default=None,
        metadata={
            "required": True,
            "searchable": True,
            "validators": [regex_validator(EMAIL_PATTERN, "email")],
        },
    )

    password: typing.Optional[str] = field(
        default=None,
        metadata={
            "required": True,
            "editable": False,
            "hidden": True,
            "deform.widget": deform.widget.PasswordWidget(),
        },
    )
    nonce: typing.Optional[str] = field(
        default_factory=lambda: secrets.token_hex(8),
        metadata={"deform.widget": deform.widget.HiddenWidget(), "hidden": True},
    )
    source: typing.Optional[str] = field(
        default="local", metadata={"validators": [valid_source]}
    )
    timezone: typing.Optional[str] = field(
        default="UTC",
        metadata={
            "validators": [valid_tz],
            "required": True,
            "deform.widget": deform.widget.Select2Widget(
                values=[(x, x) for x in pytz.all_timezones]
            ),
        },
    )
    is_administrator: typing.Optional[bool] = field(
        default=False, metadata={"searchable": True}
    )

    __unique_constraint__ = ["username", "deleted"]
