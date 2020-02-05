import colander
from .common import dataclass_get_type, dataclass_check_type
import dataclasses
from datetime import datetime, date
from dataclasses import field
from ...interfaces import ISchema
from pkg_resources import resource_filename
from importlib import import_module
from deform.widget import HiddenWidget
import copy


def colander_params(prop, oid_prefix, **kwargs):
    t = dataclass_get_type(prop)
    params = {
        "name": prop.name,
        "oid": "%s-%s" % (oid_prefix, prop.name),
        "missing": colander.required if t["required"] else colander.drop,
    }
    deform_field_config = prop.metadata.get("deform", {})
    if "widget" in deform_field_config.keys():
        params["widget"] = copy.copy(deform_field_config["widget"])
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
        params = colander_params(prop, oid_prefix, typ=colander.Mapping())
        return colander.SchemaNode(**params)
    if t["type"] == list:
        params = colander_params(prop, oid_prefix, typ=colander.List())
        return colander.SchemaNode(**params)

    raise KeyError(prop)


def dataclass_to_colander(
    schema,
    include_fields=None,
    exclude_fields=None,
    hidden_fields=None,
    colander_schema_type=colander.MappingSchema,
    oid_prefix="deformField",
):
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
