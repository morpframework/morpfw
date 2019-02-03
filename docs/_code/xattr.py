import typing
from dataclasses import dataclass
from morpfw.crud.xattrprovider.fieldxattrprovider import FieldXattrProvider
import morpfw
from .app import App
from .model import PageModel


@dataclass
class PageXattrSchema(morpfw.BaseSchema):

    field1: typing.Optional[str] = None
    field2: typing.Optional[str] = None


class PageXattrProvider(FieldXattrProvider):

    schema = PageXattrSchema
    additional_properties = False


@App.xattrprovider(model=PageModel)
def get_xattrprovider(context):
    return PageXattrProvider(context)
