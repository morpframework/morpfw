import rulez

class Reference(object):

    def __init__(self, name: str, resource_type: str, *, attribute: str = 'uuid', title=None):
        self.name = name
        self.resource_type = resource_type
        self.attribute = attribute
        self.title = title

    def resolve(self, context, request):
        value = context[self.name]
        collection = request.get_collection(self.resource_type)
        items = collection.search(rulez.field(self.attribute) == value)
        if items:
            return items[0]
        return None


class BackReference(object):

    def __init__(self, name: str, resource_type: str, reference_name: str, *, title=None, single=False):
        self.name = name
        self.resource_type = resource_type
        self.reference_name = reference_name
        self.title = title
        self.single_reference = single

    def resolve(self, context, request):
        typeinfo = request.app.config.type_registry.get_typeinfo(
            name=self.resource_type, request=request
        )
        refschema = typeinfo['schema']
        reference = None
        for ref in refschema.__references__:
            if ref.name == self.reference_name:
                reference = ref
                break
        if reference is None:
            raise ValueError('Invalid reference name. %s' % self.reference_name)

        value = context[reference.attribute]
        collection = request.get_collection(self.resource_type)
        items = collection.search(rulez.field(reference.name) == value)
        if items:
            if self.single_reference:
                return items[0]
            return items

        if self.single_reference:
            return None
        return []
