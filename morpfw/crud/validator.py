from functools import partial
from .errors import ValidationError, FormValidationError, FieldValidationError
from jsonschema import Draft4Validator
from .util import jsl_to_jsonobject, dataclass_to_jsl, dataclass_get_type
import reg
from morepath.publish import resolve_model
import urllib
import re


@reg.dispatch(reg.match_instance('model'), reg.match_instance('request'))
def get_data(model, request):
    raise NotImplementedError


def regex_validator(pattern, name):
    p = re.compile(pattern)

    def _regex_validator(value):
        if not p.match(value):
            raise FieldValidationError(
                '%s does not match %s pattern' % (value, name))

    return _regex_validator


def load(validator, schema, request):
    newreq = request.app.request_class(
        request.environ.copy(), request.app.root,
        path_info=urllib.parse.unquote(request.path))
    context = resolve_model(newreq)
    context.request = request
    if schema is None:
        dc = context.schema
    else:
        dc = schema

    data = get_data(context, request)
    dc.validate(request, data)
    return request.json


def validate_schema(validator=Draft4Validator, schema=None):
    return partial(load, validator, schema)
