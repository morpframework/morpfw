
import reg


class TypeRegistry(object):

    def __init__(self):
        self.types = []

    def register_type(self, name):
        if name not in self.types:
            self.types.append(name)

    def get_typeinfo(self, name, request):
        try:
            factory = request.app.get_typeinfo_factory(name)
        except NotImplementedError:
            factory = None

        if factory is None:
            if hasattr(request.app, 'get_authn_provider'):
                try:
                    factory = request.app.get_authn_provider(
                        request).get_typeinfo_factory(name)
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
