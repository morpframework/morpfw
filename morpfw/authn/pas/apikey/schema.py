import random
import string
import typing
from dataclasses import dataclass, field

from morpfw.crud import Schema


def random_str(length):
    ds = string.ascii_letters + "!^@_"
    out = random.sample(string.ascii_letters, 1)[0]
    for i in range(length - 1):
        out += random.sample(ds, 1)[0]
    return out


def current_userid(request, data, model):
    if data["userid"] is None:
        data["userid"] = request.identity.userid
    return data["userid"]


def generate_identity(request, data, model):
    if data["api_identity"]:
        return data["api_identity"]
    return random_str(32)


@dataclass
class APIKeySchema(Schema):

    userid: typing.Optional[str] = field(
        default=None,
        metadata={"format": "uuid", "index": True, "compute_value": current_userid,},
    )
    name: typing.Optional[str] = field(default=None, metadata={"required": True})
    api_identity: typing.Optional[str] = field(
        default=None, metadata={"compute_value": generate_identity, "index": True},
    )
    api_secret: typing.Optional[str] = field(
        default=None, metadata={"editable": False, "hidden": True}
    )
