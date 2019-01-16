from morepath.publish import resolve_model as _resolve_model
from ..interfaces import ISchema
import jsl
import jsonobject
import dataclasses
from copy import copy
import typing
from datetime import datetime, date


def resolve_model(request):
    newreq = request.app.request_class(
        request.environ.copy(), request.app, path_info=request.path)
    context = _resolve_model(newreq)
    context.request = request
    return context


def jsonobject_property_to_jsl_field(
        prop: jsonobject.JsonProperty, nullable=False) -> jsl.BaseField:
    if isinstance(prop, jsonobject.DateProperty):
        return jsl.DateTimeField(name=prop.name, required=prop.required)
    if isinstance(prop, jsonobject.DateTimeProperty):
        return jsl.DateTimeField(name=prop.name, required=prop.required)
    if isinstance(prop, jsonobject.StringProperty):
        return jsl.StringField(name=prop.name, required=prop.required)
    if isinstance(prop, jsonobject.IntegerProperty):
        return jsl.IntField(name=prop.name, required=prop.required)
    if isinstance(prop, jsonobject.FloatProperty):
        return jsl.NumberField(name=prop.name, required=prop.required)
    if isinstance(prop, jsonobject.BooleanProperty):
        return jsl.BooleanField(name=prop.name, required=prop.required)
    if isinstance(prop, jsonobject.DictProperty):
        if prop.item_wrapper:
            subtype = jsonobject_to_jsl(
                prop.item_wrapper.item_type, nullable=nullable)
            return jsl.DocumentField(name=prop.name,
                                     document_cls=subtype,
                                     required=prop.required)
        return jsl.DictField(name=prop.name, required=prop.required)
    if isinstance(prop, jsonobject.ListProperty):
        if prop.item_wrapper:
            if isinstance(prop.item_wrapper, jsonobject.ObjectProperty):
                if issubclass(prop.item_wrapper.item_type, jsonobject.JsonObject):
                    subtype = jsl.DocumentField(
                        document_cls=jsonobject_to_jsl(prop.item_wrapper.item_type), nullable=nullable)
                elif isinstance(prop.item_wrapper.item_type, jsonobject.JsonProperty):
                    subtype = jsonobject_property_to_jsl_field(
                        prop.item_wrapper.item_type)
                else:
                    raise KeyError(prop.item_wrapper.item_type)
            elif isinstance(prop.item_wrapper, jsonobject.StringProperty):
                subtype = jsl.StringField(name=prop.name)
            elif isinstance(prop.item_wrapper, jsonobject.IntegerProperty):
                subtype = jsl.IntField(name=prop.name)
            elif isinstance(prop.item_wrapper, jsonobject.FloatProperty):
                subtype = jsl.NumberField(name=prop.name)
            elif isinstance(prop.item_wrapper, jsonobject.DictProperty):
                subtype = jsl.DictField(name=prop.name)
            else:
                raise KeyError(prop.item_wrapper)
            return jsl.ArrayField(items=subtype, required=prop.required)
        return jsl.ArrayField(name=prop.name, required=prop.required)

    raise KeyError(prop)


_marker = object()


def dataclass_get_type(field):
    metadata = {
        'required': _marker,
        'exclude_if_empty': False,
        'validators': []
    }
    metadata.update(field.metadata.get('morpfw', {}))

    origin = getattr(field.type, '__origin__', None)
    required = True
    if origin == typing.Union:
        if len(field.type.__args__) == 2:
            if field.type.__args__[1] == type(None):
                required = False
            typ = field.type.__args__[0]
    else:
        typ = field.type

    if metadata['required'] is _marker:
        metadata['required'] = required

    required = metadata['required']

    origin = getattr(typ, '__origin__', None)

    if origin == list:
        if getattr(typ, '__args__', None):
            return {
                'name': field.name,
                'type': list,
                'schema': field.type.__args__[0],
                'required': required,
                'metadata': metadata
            }
        else:
            return {
                'name': field.name,
                'type': list,
                'required': required,
                'metadata': metadata
            }

    return {
        'type': typ,
        'required': required,
        'metadata': metadata
    }


def dataclass_check_type(field, basetype):

    t = dataclass_get_type(field)

    if t['type'] == basetype:
        return t

    # wtf bool is a subclass of integer?
    if t['type'] == bool and basetype == int:
        return None

    if issubclass(t['type'], basetype):
        return t

    return None


def dataclass_field_to_jsl_field(
        prop: dataclasses.Field, nullable=False) -> jsl.BaseField:
    t = dataclass_check_type(prop, date)
    if t:
        return jsl.DateTimeField(name=prop.name, required=t['required'])
    t = dataclass_check_type(prop, datetime)
    if t:
        return jsl.DateTimeField(name=prop.name, required=t['required'])
    t = dataclass_check_type(prop, str)
    if t:
        return jsl.StringField(name=prop.name, required=t['required'])
    t = dataclass_check_type(prop, int)
    if t:
        return jsl.IntField(name=prop.name, required=t['required'])
    t = dataclass_check_type(prop, float)
    if t:
        return jsl.NumberField(name=prop.name, required=t['required'])
    t = dataclass_check_type(prop, bool)
    if t:
        return jsl.BooleanField(name=prop.name, required=t['required'])
    t = dataclass_check_type(prop, dict)
    if t:
        return jsl.DictField(name=prop.name, required=t['required'])
    t = dataclass_check_type(prop, ISchema)
    if t:
        subtype = jsonobject_to_jsl(
            t['schema'], nullable=nullable)
        return jsl.DocumentField(name=prop.name,
                                 document_cls=subtype,
                                 required=t['required'])

    t = dataclass_check_type(prop, list)
    if t:
        return jsl.ArrayField(name=prop.name, required=t['required'])

    t = dataclass_check_type(prop, typing.List)
    if t:
        if 'schema' not in t.keys():
            return jsl.ArrayField(name=prop.name, required=t['required'])

        if issubclass(t['schema'], ISchema):
            subtype = jsl.DocumentField(
                document_cls=jsonobject_to_jsl(
                    t['schema'], nullable=nullable))
        elif t['schema'] == str:
            subtype = jsl.StringField(name=prop.name)
        elif t['schema'] == int:
            subtype = jsl.IntField(name=prop.name)
        elif t['schema'] == float:
            subtype = jsl.NumberField(name=prop.name)
        elif t['schema'] == dict:
            subtype = jsl.DictField(name=prop.name)
        else:
            raise KeyError(t['schema'])
        return jsl.ArrayField(items=subtype, required=t['required'])

    raise KeyError(prop)


def _set_nullable(prop):
    if not prop.required:
        return jsl.OneOfField([prop, jsl.NullField(name=prop.name)])
    return prop


def dataclass_to_jsl(schema, nullable=False):
    attrs = {}

    class Options(object):
        additional_properties = True

    for attr, prop in schema.__dataclass_fields__.items():
        prop = dataclass_field_to_jsl_field(prop, nullable=False)
        if nullable:
            attrs[attr] = _set_nullable(prop)
        else:
            if not prop.required:
                attrs[attr] = prop
            else:
                if isinstance(prop, jsl.StringField):
                    if not prop.pattern:
                        prop.pattern = '.+'
                attrs[attr] = prop

    attrs['Options'] = Options
    Schema = type("Schema", (jsl.Document, ), attrs)

    return Schema


def jsonobject_to_jsl(schema, nullable=False):
    # output jsl schema from jsonobject schema
    attrs = {}

    class Options(object):
        additional_properties = True

    for attr, prop in schema._properties_by_attr.items():
        prop = jsonobject_property_to_jsl_field(prop, nullable=nullable)
        if nullable:
            attrs[attr] = _set_nullable(prop)
        else:
            if not prop.required:
                attrs[attr] = prop
            else:
                if isinstance(prop, jsl.StringField):
                    if not prop.pattern:
                        prop.pattern = '.+'
                attrs[attr] = prop

    attrs['Options'] = Options
    Schema = type("Schema", (jsl.Document, ), attrs)

    return Schema


def jsl_nullable(schema):
    return jsonobject_to_jsl(jsl_to_jsonobject(schema), nullable=True)


def jsl_field_to_jsonobject_property(
        prop: jsl.BaseField) -> jsonobject.JsonProperty:
    if isinstance(prop, jsl.DateTimeField):
        return jsonobject.DateTimeProperty(name=prop.name,
                                           required=prop.required)
    if isinstance(prop, jsl.StringField):
        return jsonobject.StringProperty(name=prop.name,
                                         required=prop.required)
    if isinstance(prop, jsl.IntField):
        return jsonobject.IntegerProperty(name=prop.name,
                                          required=prop.required)
    if isinstance(prop, jsl.DictField):
        return jsonobject.DictProperty(name=prop.name, required=prop.required)
    if isinstance(prop, jsl.NumberField):
        return jsonobject.FloatProperty(name=prop.name, required=prop.required)
    if isinstance(prop, jsl.BooleanField):
        return jsonobject.BooleanProperty(name=prop.name,
                                          required=prop.required)
    if isinstance(prop, jsl.DocumentField):
        if prop.document_cls:
            subtype = jsl_to_jsonobject(prop.document_cls)
            return jsonobject.DictProperty(name=prop.name,
                                           item_type=subtype,
                                           required=prop.required)
        return jsonobject.DictProperty(name=prop.name, required=prop.required)
    if isinstance(prop, jsl.ArrayField):
        if prop.items:
            if isinstance(prop.items, jsl.DocumentField):
                subtype = jsl_to_jsonobject(prop.items.document_cls)
            elif isinstance(prop.items, jsl.BaseField):
                subtype = jsl_field_to_jsonobject_property(prop.items)
            else:
                raise KeyError(prop.items)
            return jsonobject.ListProperty(item_type=subtype,
                                           required=prop.required)
        return jsonobject.ListProperty(name=prop.name, required=prop.required)

    raise KeyError(prop)


def jsl_to_jsonobject(schema):
    # output jsonobject schema from jsl schema
    attrs = {}
    for attr, prop in schema._fields.items():
        prop.name = attr
        attrs[attr] = jsl_field_to_jsonobject_property(prop)

    Schema = type("Schema", (jsonobject.JsonObject, ), attrs)

    return Schema


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
                elif (isinstance(f, jsl.IntField) or
                      isinstance(f, jsl.NumberField)):
                    data[n] = None
                elif isinstance(f, jsl.DictField):
                    data[n] = {}
                elif isinstance(f, jsl.ArrayField):
                    data[n] = []

    return data
