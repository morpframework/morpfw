import jsl
import jsonobject
from inverter import jsl2jsonobject, jsonobject2jsl


class SubSchema(jsonobject.JsonObject):
    stringfield = jsonobject.StringProperty()
    intfield = jsonobject.IntegerProperty()


class SampleSchema(jsonobject.JsonObject):
    stringfield = jsonobject.StringProperty()
    intfield = jsonobject.IntegerProperty()
    dictfield = jsonobject.DictProperty()
    arrayfield = jsonobject.ListProperty()
    documentarrayfield = jsonobject.ListProperty(item_type=SubSchema)
    documentfield = jsonobject.DictProperty(item_type=SubSchema)
    datefield = jsonobject.DateProperty()
    datetimefield = jsonobject.DateTimeProperty()


def test_jsonobject_convert():
    schema = jsonobject2jsl.convert(SampleSchema)
    field = getattr(schema, "stringfield")
    assert isinstance(field, jsl.StringField)
    assert field.name == "stringfield"

    field = getattr(schema, "intfield")
    assert isinstance(field, jsl.IntField)
    assert field.name == "intfield"

    field = getattr(schema, "dictfield")
    assert isinstance(field, jsl.DictField)
    assert field.name == "dictfield"

    field = getattr(schema, "arrayfield")
    assert isinstance(field, jsl.ArrayField)
    assert field.name == "arrayfield"

    field = getattr(schema, "documentarrayfield")
    assert isinstance(field, jsl.ArrayField)
    assert isinstance(field.items, jsl.DocumentField)
    assert isinstance(field.items.document_cls.stringfield, jsl.StringField)

    field = getattr(schema, "documentfield")
    assert isinstance(field, jsl.DocumentField)
    assert isinstance(field.document_cls.stringfield, jsl.StringField)

    field = getattr(schema, "datetimefield")
    assert isinstance(field, jsl.DateTimeField)

    field = getattr(schema, "datefield")
    assert isinstance(field, jsl.DateTimeField)

    assert schema.get_schema()

    schema = jsl2jsonobject.convert(schema)
