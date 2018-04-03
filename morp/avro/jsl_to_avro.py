import jsl
import copy


def _avro_field(**kwargs):
    result = {}
    for k, v in kwargs.items():
        if v:
            result[k] = v
    return result


def jsl_field_to_avro_field(prop: jsl.BaseField, name, namespace) -> dict:
    if isinstance(prop, jsl.DateTimeField):
        return _avro_field(name=name, type='string')
    if isinstance(prop, jsl.StringField):
        return _avro_field(name=name, type='string')
    if isinstance(prop, jsl.IntField):
        return _avro_field(name=name, type='int')
    if isinstance(prop, jsl.DictField):
        return _avro_field(name=name, type='map')
    if isinstance(prop, jsl.NumberField):
        return _avro_field(name=name, type='double')
    if isinstance(prop, jsl.BooleanField):
        return _avro_field(name=name, type='boolean')
    if isinstance(prop, jsl.DocumentField):
        if prop.document_cls:
            subtype = jsl_to_avro(
                prop.document_cls, name=name, namespace='%s.%s' % (namespace, name))
            return _avro_field(name=name, type=subtype)
        return _avro_field(name=name, type='map')
    if isinstance(prop, jsl.ArrayField):
        if prop.items:
            if isinstance(prop.items, jsl.DocumentField):
                subtype = jsl_to_avro(
                    prop.items.document_cls, namespace='%s.%s' % (namespace, name))
            elif isinstance(prop.items, jsl.BaseField):
                subtype = jsl_field_to_avro_field(
                    prop.items, name=prop.name, namespace=namespace)['type']
            else:
                raise KeyError(prop.items)
            return _avro_field(name=name, type='array', items=subtype)
        return _avro_field(name=name, type='array', items='string')

    raise KeyError(prop)


def jsl_to_avro(schema, name=None, namespace='schema'):
    fields = []
    avsc = {
        'type': 'record',
    }
    if name:
        avsc['name'] = name
    if namespace:
        avsc['namespace'] = namespace
    for attr, prop in schema._fields.items():
        prop.name = attr
        fields.append(jsl_field_to_avro_field(
            prop, name=attr, namespace=namespace))

    avsc['fields'] = fields
    return avsc
