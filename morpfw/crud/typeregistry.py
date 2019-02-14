

class TypeRegistry(object):

    def __init__(self):
        self.typeinfo_factories = {}

    def register_typeinfo_factory(self, name, info_factory):
        self.typeinfo_factories[name] = info_factory

    def get_typeinfo(self, name, request):
        result = self.typeinfo_factories[name](request)
        result['name'] = name
        return result

    def get_typeinfos(self, request):
        res = {}
        for k in self.typeinfo_factories.keys():
            res[k] = self.get_typeinfo(k, request)
        return res
