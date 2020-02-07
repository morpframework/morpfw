import copy
import dataclasses
import typing
from dataclasses import field
from datetime import date, datetime
from importlib import import_module

from pkg_resources import resource_filename

import colander
import morpfw.sql
import sqlalchemy
import sqlalchemy_jsonfield as sajson
from deform.widget import HiddenWidget

from ...interfaces import ISchema
from .common import dataclass_check_type, dataclass_get_type


def sqlalchemy_params(prop, typ, **kwargs):
    t = dataclass_get_type(prop)

    params = {
        "name": prop.name,
        "type_": typ,
    }

    if not isinstance(prop.default, dataclasses._MISSING_TYPE):
        params["default"] = prop.default

    if not isinstance(prop.default_factory, dataclasses._MISSING_TYPE):
        params["default"] = prop.default_factory

    if t["metadata"].get("primary_key", None) is True:
        params["primary_key"] = True

    if t["metadata"].get("index", None) is True:
        params["index"] = True

    if t["metadata"].get("autoincrement", None) is True:
        params["autoincrement"] = True

    if t["metadata"].get("unique", None) is True:
        params["unique"] = True

    params.update(kwargs)
    return params


def dataclass_field_to_sqla_col(prop: dataclasses.Field) -> sqlalchemy.Column:
    t = dataclass_get_type(prop)
    if t["type"] == date:
        params = sqlalchemy_params(prop, typ=sqlalchemy.Date())
        return sqlalchemy.Column(**params)
    if t["type"] == datetime:
        params = sqlalchemy_params(prop, typ=sqlalchemy.DateTime(timezone=True))
        return sqlalchemy.Column(**params)
    if t["type"] == str:
        str_format = t["metadata"].get("format", None)
        if str_format == "text":
            params = sqlalchemy_params(prop, typ=sqlalchemy.Text())
        elif str_format == "uuid":
            params = sqlalchemy_params(prop, typ=morpfw.sql.GUID())
        else:
            params = sqlalchemy_params(prop, typ=sqlalchemy.String(1024))
        return sqlalchemy.Column(**params)
    if t["type"] == int:
        if t["metadata"].get("format", None) == "bigint":
            params = sqlalchemy_params(prop, typ=sqlalchemy.BigInteger())
        else:
            params = sqlalchemy_params(prop, typ=sqlalchemy.Integer())
        return sqlalchemy.Column(**params)
    if t["type"] == float:
        if t["metadata"].get("format", None) == "numeric":
            params = sqlalchemy_params(prop, typ=sqlalchemy.Numeric())
        else:
            params = sqlalchemy_params(prop, typ=sqlalchemy.Float())

        return sqlalchemy.Column(**params)
    if t["type"] == bool:
        params = sqlalchemy_params(prop, typ=sqlalchemy.Boolean())
        return sqlalchemy.Column(**params)

    if dataclass_check_type(prop, ISchema):
        raise NotImplementedError("Sub schema is not supported")

    if t["type"] == dict:
        params = sqlalchemy_params(prop, typ=sajson.JSONField())
        return sqlalchemy.Column(**params)
    if t["type"] == list:
        params = sqlalchemy_params(prop, typ=sajson.JSONField())
        return sqlalchemy.Column(**params)

    raise KeyError(prop)


def dataclass_to_pgsqla(schema, metadata, name=None) -> sqlalchemy.Table:
    if name is None:
        if getattr(schema, "__table_name__", None):
            name = schema.__table_name__
        else:
            name = schema.__name__.lower()

    cols = []

    for attr, prop in sorted(schema.__dataclass_fields__.items(), key=lambda x: x[0]):
        prop = dataclass_field_to_sqla_col(prop)
        cols.append(prop)

    Table = sqlalchemy.Table(name, metadata, *cols, extend_existing=True)

    return Table
