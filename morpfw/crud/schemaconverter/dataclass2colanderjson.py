import dataclasses
import typing
from datetime import date, datetime, timedelta

import colander
import pytz

from ...interfaces import ISchema
from .common import dataclass_check_type, dataclass_get_type
from .dataclass2colander import BindableMappingSchema, SchemaNode, colander_params
from .dataclass2colander import (
    dataclass_field_to_colander_schemanode as orig_dc2colander_node,
)
from .dataclass2colander import dataclass_to_colander

epoch_date = date(1970, 1, 1)


class Boolean(colander.Boolean):
    def deserialize(self, node, cstruct):
        if cstruct is True:
            cstruct = "true"
        elif cstruct is False:
            cstruct = "false"

        return super(Boolean, self).deserialize(node, cstruct)

    def serialize(self, node, appstruct):
        result = super(Boolean, self).serialize(node, appstruct)
        if result is colander.null:
            return None
        if result is not colander.null:
            if result.lower() == "true":
                result = True
            else:
                result = False
        return result


class Float(colander.Float):
    def deserialize(self, node, cstruct):
        if cstruct is not None:
            cstruct = str(cstruct)
        return super(Float, self).deserialize(node, cstruct)

    def serialize(self, node, appstruct):
        result = super(Float, self).serialize(node, appstruct)
        if result is colander.null:
            return None
        if result is not colander.null:
            result = float(result)
        return result


class Int(colander.Int):
    def deserialize(self, node, cstruct):
        if cstruct is not None:
            cstruct = str(cstruct)
        return super(Int, self).deserialize(node, cstruct)

    def serialize(self, node, appstruct):
        result = super(Int, self).serialize(node, appstruct)
        if result is colander.null:
            return None

        if result is not colander.null:
            result = int(result)
        return result


class Str(colander.Str):
    def deserialize(self, node, cstruct):
        if cstruct is None:
            return colander.null
        return super(Str, self).deserialize(node, cstruct)

    def serialize(self, node, appstruct):
        if appstruct is None:
            return None
        result = super(Str, self).serialize(node, appstruct)
        if result is colander.null:
            return None
        return result


class Date(colander.Date):
    def serialize(self, node, appstruct):
        result = super(Date, self).serialize(node, appstruct)
        if result is colander.null:
            return None

        return (appstruct - epoch_date).days

    def deserialize(self, node, cstruct):
        if cstruct and not isinstance(cstruct, int):
            raise colander.Invalid(
                node, "Date is expected to be number of days after 1970-01-01"
            )

        if cstruct:
            cstruct = (epoch_date + timedelta(days=cstruct)).strftime(r"%Y-%m-%d")
        return super().deserialize(node, cstruct)


class DateTime(colander.DateTime):
    def serialize(self, node, appstruct):
        if appstruct:
            appstruct = appstruct.astimezone(pytz.UTC)
        result = super(DateTime, self).serialize(node, appstruct)
        if result is colander.null:
            return None

        return int(appstruct.timestamp() * 1000)

    def deserialize(self, node, cstruct):
        if cstruct and not isinstance(cstruct, int):
            raise colander.Invalid(
                node, "DateTime is expected to in Unix timestamp in miliseconds in UTC"
            )
        if cstruct:
            cstruct = datetime.fromtimestamp(
                int(cstruct) / 1000, tz=pytz.UTC
            ).isoformat()
        return super().deserialize(node, cstruct)


def dataclass_field_to_colander_schemanode(
    prop: dataclasses.Field, schema, request, oid_prefix="deformField", mode=None,
) -> colander.SchemaNode:

    t = dataclass_get_type(prop)
    if t["type"] == date:
        params = colander_params(
            prop, oid_prefix, typ=Date(), schema=schema, request=request, mode=mode
        )
        return SchemaNode(**params)
    if t["type"] == datetime:
        params = colander_params(
            prop, oid_prefix, typ=DateTime(), schema=schema, request=request, mode=mode
        )
        return SchemaNode(**params)
    if t["type"] == str:
        params = colander_params(
            prop, oid_prefix, typ=Str(), schema=schema, request=request, mode=mode
        )
        return SchemaNode(**params)
    if t["type"] == int:
        params = colander_params(
            prop, oid_prefix, typ=Int(), schema=schema, request=request, mode=mode
        )
        return SchemaNode(**params)
    if t["type"] == float:
        params = colander_params(
            prop, oid_prefix, typ=Float(), schema=schema, request=request, mode=mode
        )
        return SchemaNode(**params)
    if t["type"] == bool:
        params = colander_params(
            prop, oid_prefix, typ=Boolean(), schema=schema, request=request, mode=mode
        )
        return SchemaNode(**params)

    if dataclass_check_type(prop, ISchema):
        subtype = dataclass_to_colanderjson(
            t["type"],
            colander_schema_type=colander.MappingSchema,
            schema=schema,
            request=request,
            mode=mode,
        )
        return subtype()

    if t["type"] == dict:
        params = colander_params(
            prop,
            oid_prefix,
            typ=colander.Mapping(unknown="preserve"),
            schema=schema,
            request=request,
            mode=mode,
        )
        return SchemaNode(**params)

    return orig_dc2colander_node(prop, oid_prefix, request)


def dataclass_to_colanderjson(
    schema,
    include_fields: typing.List[str] = None,
    exclude_fields: typing.List[str] = None,
    hidden_fields: typing.List[str] = None,
    readonly_fields: typing.List[str] = None,
    include_schema_validators: bool = True,
    colander_schema_type: typing.Type[colander.Schema] = BindableMappingSchema,
    oid_prefix: str = "deformField",
    request=None,
    mode="default",
) -> typing.Type[colander.MappingSchema]:
    return dataclass_to_colander(
        schema,
        request=request,
        include_fields=include_fields,
        exclude_fields=exclude_fields,
        hidden_fields=hidden_fields,
        readonly_fields=readonly_fields,
        include_schema_validators=include_schema_validators,
        colander_schema_type=colander_schema_type,
        oid_prefix=oid_prefix,
        dataclass_field_to_colander_schemanode=dataclass_field_to_colander_schemanode,
        mode=mode,
    )
