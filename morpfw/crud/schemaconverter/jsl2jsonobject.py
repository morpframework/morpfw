import jsonobject
import jsl


def jsl_field_to_jsonobject_property(prop: jsl.BaseField) -> jsonobject.JsonProperty:
    if isinstance(prop, jsl.DateTimeField):
        return jsonobject.DateTimeProperty(name=prop.name, required=prop.required)
    if isinstance(prop, jsl.StringField):
        return jsonobject.StringProperty(name=prop.name, required=prop.required)
    if isinstance(prop, jsl.IntField):
        return jsonobject.IntegerProperty(name=prop.name, required=prop.required)
    if isinstance(prop, jsl.DictField):
        return jsonobject.DictProperty(name=prop.name, required=prop.required)
    if isinstance(prop, jsl.NumberField):
        return jsonobject.FloatProperty(name=prop.name, required=prop.required)
    if isinstance(prop, jsl.BooleanField):
        return jsonobject.BooleanProperty(name=prop.name, required=prop.required)
    if isinstance(prop, jsl.DocumentField):
        if prop.document_cls:
            subtype = jsl_to_jsonobject(prop.document_cls)
            return jsonobject.DictProperty(
                name=prop.name, item_type=subtype, required=prop.required
            )
        return jsonobject.DictProperty(name=prop.name, required=prop.required)
    if isinstance(prop, jsl.ArrayField):
        if prop.items:
            if isinstance(prop.items, jsl.DocumentField):
                subtype = jsl_to_jsonobject(prop.items.document_cls)
            elif isinstance(prop.items, jsl.BaseField):
                subtype = jsl_field_to_jsonobject_property(prop.items)
            else:
                raise KeyError(prop.items)
            return jsonobject.ListProperty(item_type=subtype, required=prop.required)
        return jsonobject.ListProperty(name=prop.name, required=prop.required)

    raise KeyError(prop)


def jsl_to_jsonobject(schema):
    # output jsonobject schema from jsl schema
    attrs = {}
    for attr, prop in schema._fields.items():
        prop.name = attr
        attrs[attr] = jsl_field_to_jsonobject_property(prop)

    Schema = type("Schema", (jsonobject.JsonObject,), attrs)

    return Schema

