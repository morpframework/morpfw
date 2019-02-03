import typing
from ..util import dataclass_to_jsl
from ...interfaces import IXattrProvider
from jsonschema import validate, ValidationError

_marker = object()


class XattrProvider(IXattrProvider):

    schema: typing.Type[typing.Any]
    additional_properties = False

    def __init__(self, context):
        self.context = context
        self.request = context.request
        self.app = context.request.app

    def jsonschema(self):
        schema = dataclass_to_jsl(
            self.schema, nullable=True,
            additional_properties=self.additional_properties
        ).get_schema(ordered=True)
        return {
            'schema': schema
        }

    def process_update(self, newdata: dict):
        data = self.as_json()
        data.update(newdata)
        self.schema.validate(self.request, data)
        self.update(data)
