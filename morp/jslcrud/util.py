from morepath.publish import resolve_model as _resolve_model
import jsl


def resolve_model(request):
    newreq = request.app.request_class(
        request.environ.copy(), request.app, path_info=request.path)
    context = _resolve_model(newreq)
    context.request = request
    return context


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
                    data[n] = ''
                elif (isinstance(f, jsl.IntField) or
                      isinstance(f, jsl.NumberField)):
                    data[n] = 0
                elif isinstance(f, jsl.DictField):
                    data[n] = {}
                elif isinstance(f, jsl.ArrayField):
                    data[n] = []

    return data
