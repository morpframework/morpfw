import typing
from dataclasses import dataclass, field

from morpfw.crud import Schema


@dataclass
class APIKeySchema(Schema):

    userid: typing.Optional[str] = None
    name: typing.Optional[str] = None
    api_identity: typing.Optional[str] = None
    api_secret: typing.Optional[str] = None
