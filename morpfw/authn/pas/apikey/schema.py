import random
import secrets
import string
import typing
from dataclasses import dataclass, field

from morpfw.crud import Schema


def current_userid(request, data, model):
    if data["userid"] is None:
        data["userid"] = request.identity.userid
    return data["userid"]


def generate_identity(request, data, model) -> str:
    if data["api_identity"]:
        return data["api_identity"]
    return secrets.token_urlsafe(32)


@dataclass
class APIKeySchema(Schema):

    userid: typing.Optional[str] = field(
        default=None,
        metadata={"format": "uuid", "index": True, "compute_value":
            current_userid, 'editable': False, 'initializable': False},
    )
    name: typing.Optional[str] = field(default=None, metadata={"required": True})
    api_identity: typing.Optional[str] = field(
        default=None, metadata={"compute_value": generate_identity, "index":
            True, 'initializable': False, 'editable': False},
    )
    api_secret: typing.Optional[str] = field(
        default=None, metadata={"editable": False, "hidden": True,
            'initializable':False}
    )
