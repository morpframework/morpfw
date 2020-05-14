import datetime
import typing

from ...interfaces import ISchema
from .common import dataclass_check_type, dataclass_get_type


def dataclass_field_to_avsc_field(prop, schema, request):
    t = dataclass_get_type(prop)
    field = {"name": prop.name}

    if t["type"] == str and prop.metadata.get("format", None) == "uuid":
        field["type"] = [{"type": "string", "logicalType": "uuid"}]
        return field

    if t["type"] == str:
        field["type"] = ["string", "null"]
        return field

    if t["type"] == int:
        field["type"] = ["int", "null"]
        return field

    if t["type"] == float:
        field["type"] = ["double", "null"]
        return field

    if t["type"] == bool:
        field["type"] = ["boolean", "null"]
        return field

    if t["type"] == datetime.datetime:
        field["type"] = [{"type": "long", "logicalType": "timestamp-millis",}, "null"]
        return field

    if t["type"] == datetime.date:
        field["type"] = [{"type": "int", "logicalType": "date",}, "null"]
        return field

    if dataclass_check_type(prop, ISchema):
        subtype = dataclass_to_avsc(prop, request=request)
        return subtype

    if t["type"] == dict:
        field["type"] = ["string", "null"]
        # encode as json
        return field
    raise TypeError("Unknown Avro type for %s" % t["type"])


def dataclass_to_avsc(
    schema,
    request,
    include_fields: typing.List[str] = None,
    exclude_fields: typing.List[str] = None,
    namespace="morpcc",
):
    result = {
        "namespace": namespace,
        "type": "record",
        "name": str(schema.__class__.__name__),
        "fields": [],
    }
    for attr, prop in schema.__dataclass_fields__.items():
        field = dataclass_field_to_avsc_field(prop, schema=schema, request=request)
        result["fields"].append(field)

    return result
