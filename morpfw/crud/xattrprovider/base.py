import typing

from inverter import dc2jsl
from jsonschema import ValidationError, validate

from ...interfaces import IXattrProvider

_marker = object()


class XattrProvider(IXattrProvider):

    schema: typing.Type[typing.Any]
    additional_properties = False

    def __init__(self, context):
        self.context = context
        self.request = context.request
        self.app = context.request.app

    def jsonschema(self):
        schema = dc2jsl.convert(
            self.schema,
            ignore_required=True,
            additional_properties=self.additional_properties,
        ).get_schema(ordered=True)
        return {"schema": schema}

    def process_update(self, newdata: dict):
        data = self.as_json()
        data.update(newdata)
        self.schema.validate(self.request, data, context=self.context)
        self.update(data)
