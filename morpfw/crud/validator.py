import re
import urllib
from functools import partial

import reg
from jsonschema import Draft4Validator
from morepath.publish import resolve_model

from .errors import FieldValidationError, FormValidationError, ValidationError
from .schemaconverter.common import dataclass_get_type
from .schemaconverter.dataclass2jsl import dataclass_to_jsl
from .schemaconverter.jsl2jsonobject import jsl_to_jsonobject


@reg.dispatch(reg.match_instance("model"), reg.match_instance("request"))
def get_data(model, request):
    raise NotImplementedError


def regex_validator(pattern, name):
    p = re.compile(pattern)

    def _regex_validator(field, value):
        if not p.match(value):
            raise FieldValidationError(
                field, "%s does not match %s pattern" % (value, name)
            )

    return _regex_validator


def load(validator, schema, request):
    newreq = request.app.request_class(
        request.environ.copy(),
        request.app.root,
        path_info=urllib.parse.unquote(request.path),
    )
    context = resolve_model(newreq)
    context.request = request
    if schema is None:
        dc = context.schema
    else:
        dc = schema

    data = get_data(context, request)
    return dc.validate(request, data)


def validate_schema(validator=Draft4Validator, schema=None):
    return partial(load, validator, schema)
