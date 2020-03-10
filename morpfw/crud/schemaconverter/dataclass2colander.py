import copy
import dataclasses
import typing
from dataclasses import field
from datetime import date, datetime
from importlib import import_module

from pkg_resources import resource_filename

import colander
from deform.schema import default_widget_makers
from deform.widget import HiddenWidget, TextAreaWidget, TextInputWidget

from ...interfaces import ISchema
from .common import dataclass_check_type, dataclass_get_type


def replace_colander_null(appstruct, value=None):
    out = {}
    for k, v in appstruct.items():
        if isinstance(v, dict):
            out[k] = replace_colander_null(v)
        elif isinstance(v, list):
            out[k] = list(map(lambda x: x if x != colander.null else value, v))
        else:
            out[k] = v if v != colander.null else value
    return out


class ValidatorsWrapper(object):
    def __init__(self, validators, request, schema, mode=None):
        self.request = request
        self.schema = schema
        self.mode = mode
        self.validators = validators

    def __call__(self, node, value):
        for validator in self.validators:
            error = validator(
                request=self.request,
                schema=self.schema,
                field=node.name,
                value=value,
                mode=self.mode,
            )
            if error:
                raise colander.Invalid(node, error)


class PreparersWrapper(object):
    def __init__(self, preparers, request, schema, mode=None):
        self.preparers = preparers
        self.request = request
        self.schema = schema
        self.mode = mode

    def __call__(self, value):
        for preparer in self.preparers:
            value = preparer(
                request=self.request, schema=self.schema, value=value, mode=self.mode
            )
        return value


class SchemaNode(colander.SchemaNode):
    def serialize(self, appstruct=colander.null):
        # workaround with deform serialization issue with colander.drop
        if appstruct is colander.null:
            appstruct = self.default
        if appstruct is colander.drop:
            appstruct = colander.null
        if isinstance(appstruct, colander.deferred):
            appstruct = colander.null

        cstruct = self.typ.serialize(self, appstruct)
        return cstruct


def colander_params(prop, oid_prefix, schema, request, mode=None, **kwargs):
    t = dataclass_get_type(prop)

    params = {
        "name": prop.name,
        "oid": "%s-%s" % (oid_prefix, prop.name),
        "missing": colander.required if t["required"] else colander.drop,
    }

    if (
        not isinstance(prop.default, dataclasses._MISSING_TYPE)
        and prop.default is not None
    ):
        params["default"] = prop.default
    elif not t["required"]:
        params["default"] = colander.drop

    if "deform.widget" in prop.metadata.keys():
        params["widget"] = copy.copy(prop.metadata["deform.widget"])

    validators = prop.metadata.get("validators", None)
    if validators:
        params["validator"] = ValidatorsWrapper(
            validators, schema=schema, request=request, mode=mode
        )

    preparers = prop.metadata.get("preparers", None)
    if preparers:
        params["preparer"] = PreparersWrapper(
            preparers, schema=schema, request=request, mode=mode
        )

    title = prop.metadata.get("title", None)

    if title:
        params["title"] = title

    description = prop.metadata.get("description", None)
    if description:
        params["description"] = description

    params.update(kwargs)
    return params


def dataclass_field_to_colander_schemanode(
    prop: dataclasses.Field, schema, request, oid_prefix="deformField", mode=None
) -> colander.SchemaNode:

    t = dataclass_get_type(prop)
    if t["type"] == date:
        params = colander_params(
            prop,
            oid_prefix,
            typ=colander.Date(),
            schema=schema,
            request=request,
            mode=mode,
        )
        return SchemaNode(**params)
    if t["type"] == datetime:
        params = colander_params(
            prop,
            oid_prefix,
            typ=colander.DateTime(),
            schema=schema,
            request=request,
            mode=mode,
        )

        return SchemaNode(**params)
    if t["type"] == str:
        params = colander_params(
            prop,
            oid_prefix,
            typ=colander.String(),
            schema=schema,
            request=request,
            mode=mode,
        )
        return SchemaNode(**params)
    if t["type"] == int:
        params = colander_params(
            prop,
            oid_prefix,
            typ=colander.Integer(),
            schema=schema,
            request=request,
            mode=mode,
        )
        return SchemaNode(**params)
    if t["type"] == float:
        params = colander_params(
            prop,
            oid_prefix,
            typ=colander.Float(),
            schema=schema,
            request=request,
            mode=mode,
        )
        return SchemaNode(**params)
    if t["type"] == bool:
        params = colander_params(
            prop,
            oid_prefix,
            typ=colander.Boolean(),
            schema=schema,
            request=request,
            mode=mode,
        )
        return SchemaNode(**params)

    if dataclass_check_type(prop, ISchema):
        subtype = dataclass_to_colander(
            t["type"],
            request=request,
            colander_schema_type=colander.MappingSchema,
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
    if t["type"] == list:
        params = colander_params(
            prop,
            oid_prefix,
            typ=colander.List(),
            schema=schema,
            request=request,
            mode=mode,
        )
        return SchemaNode(**params)

    raise KeyError(prop)


def dataclass_to_colander(
    schema,
    request,
    mode="default",
    include_fields: typing.List[str] = None,
    exclude_fields: typing.List[str] = None,
    hidden_fields: typing.List[str] = None,
    readonly_fields: typing.List[str] = None,
    colander_schema_type: typing.Type[colander.Schema] = colander.MappingSchema,
    oid_prefix: str = "deformField",
    dataclass_field_to_colander_schemanode=dataclass_field_to_colander_schemanode,
) -> typing.Type[colander.MappingSchema]:
    # output colander schema from dataclass schema
    attrs = {}

    include_fields = include_fields or []
    exclude_fields = exclude_fields or []
    hidden_fields = hidden_fields or []
    readonly_fields = readonly_fields or []

    if mode == "edit":
        readonly_fields += [
            attr
            for attr, prop in schema.__dataclass_fields__.items()
            if (
                not prop.metadata.get("editable", True)
                or prop.metadata.get("readonly", False)
            )
        ]
    elif mode == "edit-process":
        exclude_fields += [
            attr
            for attr, prop in schema.__dataclass_fields__.items()
            if (
                not prop.metadata.get("editable", True)
                or prop.metadata.get("readonly", False)
            )
        ]
    else:
        readonly_fields += [
            attr
            for attr, prop in schema.__dataclass_fields__.items()
            if (prop.metadata.get("readonly", False))
        ]

    if include_fields:
        for attr, prop in schema.__dataclass_fields__.items():
            if prop.name in include_fields and prop.name not in exclude_fields:
                prop = dataclass_field_to_colander_schemanode(
                    prop,
                    oid_prefix=oid_prefix,
                    schema=schema,
                    request=request,
                    mode=mode,
                )
                attrs[attr] = prop
    else:
        for attr, prop in schema.__dataclass_fields__.items():
            if prop.name not in exclude_fields:
                prop = dataclass_field_to_colander_schemanode(
                    prop,
                    oid_prefix=oid_prefix,
                    schema=schema,
                    request=request,
                    mode=mode,
                )
                attrs[attr] = prop

    for attr, prop in attrs.items():
        dcprop = schema.__dataclass_fields__[attr]

        t = dataclass_get_type(dcprop)
        if attr in hidden_fields:
            if prop.widget is None:
                prop.widget = HiddenWidget()
            else:
                prop.widget.hidden = True

        if attr in readonly_fields:
            if prop.widget is None:
                prop_widget = default_widget_makers.get(prop.typ.__class__, None)
                if prop_widget is None:
                    prop_widget = TextInputWidget
                prop.widget = prop_widget()

            prop.widget.readonly = True

        if t["type"] == str:
            if dcprop.metadata.get("format", None) == "text":
                if prop.widget is None:
                    prop.widget = TextAreaWidget()

    def validator(self, node, appstruct):
        vdata = replace_colander_null(appstruct)
        for form_validator in getattr(schema, "__validators__", []):
            fe = form_validator(request, vdata)
            if fe:
                raise colander.Invalid(node[fe["field"]], fe["message"])
        for form_validator in request.app.get_formvalidators(schema):
            fe = form_validator(request, vdata)
            if fe:
                raise colander.Invalid(node[fe["field"]], fe["message"])

    attrs["validator"] = validator
    Schema = type("Schema", (colander_schema_type,), attrs)

    return Schema
