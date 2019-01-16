from morpfw.crud import Schema
from dataclasses import dataclass, field
import typing


@dataclass
class APIKeySchema(Schema):

    userid: typing.Optional[str] = None
    label: typing.Optional[str] = None
    api_identity: typing.Optional[str] = None
    api_secret: typing.Optional[str] = None
