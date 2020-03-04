import typing
from dataclasses import dataclass, field
from datetime import datetime
from pprint import pprint
from uuid import uuid4

import colander
import pytz

from ..interfaces import ISchema
from .app import App
from .errors import FieldValidationError, FormValidationError, ValidationError
from .schemaconverter.common import dataclass_get_type
from .schemaconverter.dataclass2colander import dataclass_to_colander
from .schemaconverter.dataclass2colanderjson import dataclass_to_colanderjson


@dataclass
class BaseSchema(ISchema):
    @classmethod
    def validate(cls, request, data, deserialize=True, json=True, update_mode=False):
        params = {}
        if deserialize:
            if not update_mode:
                if json:
                    cschema = dataclass_to_colanderjson(cls, request=request)
                else:
                    cschema = dataclass_to_colander(cls, request=request)

            else:
                if json:
                    cschema = dataclass_to_colanderjson(
                        cls, include_fields=data.keys(), request=request, mode="update"
                    )
                else:
                    cschema = dataclass_to_colander(
                        cls, include_fields=data.keys(), request=request, mode="update"
                    )
            try:
                data = cschema().deserialize(data)
            except colander.Invalid as e:
                errors = e.asdict()
                params["field_errors"] = [
                    FieldValidationError(path=k, message=m) for k, m in errors.items()
                ]
        else:
            # field errors
            for k, f in cls.__dataclass_fields__.items():
                t = dataclass_get_type(f)
                error = None
                for validate in t["metadata"]["validators"]:
                    if update_mode:
                        val = data.get(k, None)
                        if val:
                            error = validate(
                                request=request,
                                schema=cls,
                                field=k,
                                value=val,
                                mode="update",
                            )
                    else:
                        val = data.get(k, None)
                        if val:
                            error = validate(
                                request=request, schema=cls, field=k, value=val
                            )
                    if error:
                        params.setdefault("field_errors", [])
                        params["field_errors"].append(
                            FieldValidationError(path=k, message=error)
                        )
                        break

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

        return data


@dataclass
class Schema(BaseSchema):

    id: typing.Optional[int] = field(
        default=None, metadata={"primary_key": True, "autoincrement": True}
    )
    uuid: typing.Optional[str] = field(
        default_factory=lambda: uuid4().hex,
        metadata={"format": "uuid", "index": True, "unique": True},
    )
    creator: typing.Optional[str] = None
    created: typing.Optional[datetime] = field(
        default_factory=lambda: datetime.now(tz=pytz.UTC), metadata={"index": True}
    )
    modified: typing.Optional[datetime] = field(
        default_factory=lambda: datetime.now(tz=pytz.UTC), metadata={"index": True}
    )
    state: typing.Optional[str] = field(default=None, metadata={"index": True})
    deleted: typing.Optional[datetime] = field(default=None, metadata={"index": True})

    blobs: typing.Optional[dict] = field(
        default_factory=dict, metadata={"exclude_if_empty": True}
    )
    xattrs: typing.Optional[dict] = field(
        default_factory=dict, metadata={"exclude_if_empty": True}
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
