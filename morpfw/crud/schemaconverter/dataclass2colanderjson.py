import dataclasses
import typing
from datetime import date, datetime

import colander
import pytz

from ...interfaces import ISchema
from .common import dataclass_check_type, dataclass_get_type
from .dataclass2colander import SchemaNode, colander_params
from .dataclass2colander import (
    dataclass_field_to_colander_schemanode as orig_dc2colander_node,
)
from .dataclass2colander import dataclass_to_colander


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
            result = bool(result)
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
        return result


class DateTime(colander.DateTime):
    def serialize(self, node, appstruct):
        if appstruct:
            appstruct = appstruct.astimezone(pytz.UTC)
        result = super(DateTime, self).serialize(node, appstruct)
        if result is colander.null:
            return None
        return result


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

    return orig_dc2colander_node(prop, oid_prefix)


def dataclass_to_colanderjson(
    schema,
    include_fields: typing.List[str] = None,
    exclude_fields: typing.List[str] = None,
    hidden_fields: typing.List[str] = None,
    colander_schema_type: typing.Type[colander.Schema] = colander.MappingSchema,
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
        colander_schema_type=colander_schema_type,
        oid_prefix=oid_prefix,
        dataclass_field_to_colander_schemanode=dataclass_field_to_colander_schemanode,
        mode=mode,
    )
