import typing
from dataclasses import dataclass
from morpfw.crud.xattrprovider.fieldxattrprovider import FieldXattrProvider
from .app import app
from .model import PageModel


@dataclass
class MyXattrSchema(object):

    field1: typing.Optional[str] = None
    field2: typing.Optional[str] = None


class MyXattrProvider(FieldXattrProvider):

    schema = MyXAttrSchema
    additional_properties = False


@App.xattrprovider(model=PageModel)
def get_xattrprovider(context):
    return MyXAttrProvider(context)
