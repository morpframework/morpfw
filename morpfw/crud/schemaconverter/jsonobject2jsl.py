import jsonobject
import jsl


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
                        prop.pattern = ".+"
                attrs[attr] = prop

    attrs["Options"] = Options
    Schema = type("Schema", (jsl.Document,), attrs)

    return Schema


def jsonobject_property_to_jsl_field(
    prop: jsonobject.JsonProperty, nullable=False
) -> jsl.BaseField:
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
            subtype = jsonobject_to_jsl(prop.item_wrapper.item_type, nullable=nullable)
            return jsl.DocumentField(
                name=prop.name, document_cls=subtype, required=prop.required
            )
        return jsl.DictField(name=prop.name, required=prop.required)
    if isinstance(prop, jsonobject.ListProperty):
        if prop.item_wrapper:
            if isinstance(prop.item_wrapper, jsonobject.ObjectProperty):
                if issubclass(prop.item_wrapper.item_type, jsonobject.JsonObject):
                    subtype = jsl.DocumentField(
                        document_cls=jsonobject_to_jsl(prop.item_wrapper.item_type),
                        nullable=nullable,
                    )
                elif isinstance(prop.item_wrapper.item_type, jsonobject.JsonProperty):
                    subtype = jsonobject_property_to_jsl_field(
                        prop.item_wrapper.item_type
                    )
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

