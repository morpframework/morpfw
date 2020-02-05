import typing
from dataclasses import dataclass, field
from datetime import datetime
from pprint import pprint
from uuid import uuid4

import colander

from ..interfaces import ISchema
from .app import App
from .errors import FieldValidationError, FormValidationError, ValidationError
from .schemaconverter.common import dataclass_get_type
from .schemaconverter.dataclass2colander import dataclass_to_colander


@dataclass
class BaseSchema(ISchema):
    @classmethod
    def validate(cls, request, data, deserialize=True, update_mode=False):
        params = {}
        if deserialize:
            if not update_mode:
                cschema = dataclass_to_colander(cls)
            else:
                cschema = dataclass_to_colander(cls, include_fields=data.keys())
            try:
                data = cschema().deserialize(data)
            except colander.Invalid as e:
                errors = e.asdict()
                params["field_errors"] = [
                    FieldValidationError(path=k, message=m) for k, m in errors.items()
                ]

        form_validators = request.app.get_formvalidators(cls)
        form_errors = []
        for form_validator in form_validators:
            fe = form_validator(request, data)
            if fe:
                form_errors.append(FormValidationError(fe))

        if form_errors:
            params["form_errors"] = form_errors

        if params:
            raise ValidationError(**params)

        # field errors
        for k, f in cls.__dataclass_fields__.items():
            t = dataclass_get_type(f)
            for validate in t["metadata"]["validators"]:
                if update_mode:
                    val = data.get(k, None)
                    if val:
                        validate(k, val)
                else:
                    validate(k, data[k])
        return data


@dataclass
class Schema(BaseSchema):

    id: typing.Optional[int] = None
    uuid: typing.Optional[str] = field(default_factory=lambda: uuid4().hex)
    creator: typing.Optional[str] = None
    created: typing.Optional[datetime] = None
    modified: typing.Optional[datetime] = None
    state: typing.Optional[str] = None
    deleted: typing.Optional[datetime] = None
    blobs: typing.Optional[dict] = field(
        default_factory=dict, metadata={"morpfw": {"exclude_if_empty": True}}
    )
    xattrs: typing.Optional[dict] = field(
        default_factory=dict, metadata={"morpfw": {"exclude_if_empty": True}}
    )


@App.identifierfield(schema=Schema)
def identifierfield(schema):
    return "uuid"


@App.default_identifier(schema=Schema)
def default_identifier(schema, obj, request):
    idfield = request.app.get_identifierfield(schema)
    if idfield == "uuid":
        return uuid4().hex
    return obj[idfield]
