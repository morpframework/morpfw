from functools import partial
from .errors import ValidationError, FormValidationError
from jsonschema import Draft4Validator
from .util import jsl_to_jsonobject, jsonobject_to_jsl
import reg
from morepath.publish import resolve_model
import urllib


@reg.dispatch(reg.match_instance('model'), reg.match_instance('request'))
def get_data(model, request):
    raise NotImplementedError


def load(validator, request):
    newreq = request.app.request_class(
        request.environ.copy(), request.app,
        path_info=urllib.parse.unquote(request.path))
    context = resolve_model(newreq)
    context.request = request
    jso = jsl_to_jsonobject(context.schema)
    jslschema = jsonobject_to_jsl(jso, nullable=True)
    schema = jslschema.get_schema(ordered=True)
    form_validators = request.app.get_jslcrud_formvalidators(context.schema)
    params = {}

    validator.check_schema(schema)
    v = validator(schema)
    data = get_data(context, request)
    field_errors = sorted(v.iter_errors(data), key=lambda e: e.path)
    if field_errors:
        params['field_errors'] = field_errors
    form_errors = []
    for form_validator in form_validators:
        e = form_validator(request, request.json)
        if e:
            form_errors.append(FormValidationError(e))

    if form_errors:
        params['form_errors'] = form_errors

    if params:
        raise ValidationError(**params)

    return request.json


def validate_schema(validator=Draft4Validator):
    return partial(load, validator)
