
import reg


class TypeRegistry(object):

    def __init__(self):
        self.types = []
        self.schema_name = {}

    def register_type(self, name, schema):
        if name not in self.types:
            self.types.append(name)
        self.schema_name[schema] = name

    def get_typeinfo(self, name, request):
        try:
            factory = request.app.get_typeinfo_factory(name)
        except NotImplementedError:
            factory = None

        if factory is None:
            raise KeyError('No type info registered for %s' % name)

        result = factory(request)  # self.typeinfo_factories[name](request)
        result['name'] = name
        return result

    def get_typeinfos(self, request):
        res = {}
        for k in self.types:
            res[k] = self.get_typeinfo(k, request)
        return res

    def get_typeinfo_by_schema(self, schema, request):
        name = self.schema_name.get(schema, None)
        if name is None:
            raise KeyError('No type info registered for %s' % schema)
        return self.get_typeinfo(name, request)
