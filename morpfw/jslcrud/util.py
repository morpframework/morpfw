from morepath.publish import resolve_model as _resolve_model
import jsl
import jsonobject
from copy import copy


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


def _set_nullable(prop):
    if not prop.required:
        return jsl.OneOfField([prop, jsl.NullField(name=prop.name)])
    return prop


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
