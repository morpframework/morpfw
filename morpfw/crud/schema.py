from uuid import uuid4
from ..interfaces import ISchema
from .app import App
from dataclasses import dataclass, field
from datetime import datetime
import typing
from .schemaconverter.common import dataclass_get_type
from .schemaconverter.dataclass2jsl import dataclass_to_jsl
from jsonschema import Draft4Validator
from .errors import ValidationError, FormValidationError, FieldValidationError
from pprint import pprint


@dataclass
class BaseSchema(ISchema):
    @classmethod
    def validate(cls, request, data, additional_properties=False, update_mode=False):
        validator = Draft4Validator
        jslschema = dataclass_to_jsl(
            cls,
            nullable=True,
            additional_properties=additional_properties,
            update_mode=update_mode,
        )
        schema = jslschema.get_schema(ordered=True)
        form_validators = request.app.get_formvalidators(cls)
        params = {}

        validator.check_schema(schema)
        v = validator(schema)
        field_errors = sorted(v.iter_errors(data), key=lambda e: e.path)
        if field_errors:
            params["field_errors"] = field_errors
        form_errors = []
        for form_validator in form_validators:
            e = form_validator(request, data)
            if e:
                form_errors.append(FormValidationError(e))

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
                        validate(val)
                else:
                    validate(data[k])
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
