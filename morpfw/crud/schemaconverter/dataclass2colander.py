import copy
import dataclasses
import typing
from dataclasses import field
from datetime import date, datetime
from importlib import import_module

from pkg_resources import resource_filename

import colander
from deform.widget import HiddenWidget

from ...interfaces import ISchema
from .common import dataclass_check_type, dataclass_get_type


def colander_params(prop, oid_prefix, **kwargs):
    t = dataclass_get_type(prop)
    default = colander.drop
    if (
        not isinstance(prop.default, dataclasses._MISSING_TYPE)
        and prop.default is not None
    ):
        default = prop.default

    params = {
        "name": prop.name,
        "oid": "%s-%s" % (oid_prefix, prop.name),
        "default": default,
        "missing": colander.required if t["required"] else colander.drop,
    }

    if 'deform.widget' in prop.metadata.keys():
        params['widget'] = copy.copy(prop.metadata['deform.widget'])

    params.update(kwargs)
    return params


def dataclass_field_to_colander_schemanode(
    prop: dataclasses.Field, oid_prefix="deformField"
) -> colander.SchemaNode:

    t = dataclass_get_type(prop)
    if t["type"] == date:
        params = colander_params(prop, oid_prefix, typ=colander.Date())
        return colander.SchemaNode(**params)
    if t["type"] == datetime:
        params = colander_params(prop, oid_prefix, typ=colander.DateTime())
        return colander.SchemaNode(**params)
    if t["type"] == str:
        params = colander_params(prop, oid_prefix, typ=colander.String())
        return colander.SchemaNode(**params)
    if t["type"] == int:
        params = colander_params(prop, oid_prefix, typ=colander.Integer())
        return colander.SchemaNode(**params)
    if t["type"] == float:
        params = colander_params(prop, oid_prefix, typ=colander.Float())
        return colander.SchemaNode(**params)
    if t["type"] == bool:
        params = colander_params(prop, oid_prefix, typ=colander.Boolean())
        return colander.SchemaNode(**params)

    if dataclass_check_type(prop, ISchema):
        subtype = dataclass_to_colander(
            t["type"], colander_schema_type=colander.MappingSchema
        )

        return subtype()
    if t["type"] == dict:
        params = colander_params(
            prop, oid_prefix, typ=colander.Mapping(unknown="preserve")
        )
        return colander.SchemaNode(**params)
    if t["type"] == list:
        params = colander_params(prop, oid_prefix, typ=colander.List())
        return colander.SchemaNode(**params)

    raise KeyError(prop)


def dataclass_to_colander(
    schema,
    include_fields: typing.List[str] = None,
    exclude_fields: typing.List[str] = None,
    hidden_fields: typing.List[str] = None,
    colander_schema_type: typing.Type[colander.Schema] = colander.MappingSchema,
    oid_prefix: str = "deformField",
    dataclass_field_to_colander_schemanode=dataclass_field_to_colander_schemanode,
) -> typing.Type[colander.MappingSchema]:
    # output colander schema from dataclass schema
    attrs = {}

    include_fields = include_fields or []
    exclude_fields = exclude_fields or []
    hidden_fields = hidden_fields or []

    if include_fields:
        for attr, prop in schema.__dataclass_fields__.items():
            if prop.name in include_fields and prop.name not in exclude_fields:
                prop = dataclass_field_to_colander_schemanode(
                    prop, oid_prefix=oid_prefix
                )
                attrs[attr] = prop
    else:
        for attr, prop in schema.__dataclass_fields__.items():
            if prop.name not in exclude_fields:
                prop = dataclass_field_to_colander_schemanode(
                    prop, oid_prefix=oid_prefix
                )
                attrs[attr] = prop

    for attr, prop in attrs.items():
        if attr in hidden_fields:
            if prop.widget is None:
                prop.widget = HiddenWidget()
            else:
                prop.widget.hidden = True

    Schema = type("Schema", (colander_schema_type,), attrs)

    return Schema
