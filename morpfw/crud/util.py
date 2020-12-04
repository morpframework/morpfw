import re
from morepath.publish import resolve_model as _resolve_model
from ..interfaces import ISchema
import jsl
import dataclasses
from copy import copy
import typing
from datetime import datetime, date


def resolve_model(request):
    newreq = request.app.request_class(
        request.environ.copy(), request.app, path_info=request.path
    )
    context = _resolve_model(newreq)
    context.request = request
    return context


_marker = object()


def generate_default(schema):
    data = {}
    if isinstance(schema, jsl.DocumentField):
        schema = schema.document_cls
    for n, f in schema._fields.items():
        if isinstance(f, jsl.DocumentField):
            data[n] = generate_default(f)

        else:
            data[n] = f.get_default()
            if data[n] is None:
                if isinstance(f, jsl.StringField):
                    data[n] = None
                elif isinstance(f, jsl.IntField) or isinstance(f, jsl.NumberField):
                    data[n] = None
                elif isinstance(f, jsl.DictField):
                    data[n] = {}
                elif isinstance(f, jsl.ArrayField):
                    data[n] = []

    return data

