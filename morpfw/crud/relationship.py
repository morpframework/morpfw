import rulez


class Reference(object):
    def __init__(
        self,
        name: str,
        resource_type: str,
        *,
        attribute: str = "uuid",
        title=None,
        metadata=None,
    ):
        self.name = name
        self.resource_type = resource_type
        self.attribute = attribute
        self.title = title
        self.metadata = metadata or {}

    def collection(self, request):
        return request.get_collection(self.resource_type)

    def get_title(self, request):
        typeinfo = request.get_typeinfo(self.resource_type)
        return self.title or typeinfo["title"]


class ReferenceResolver(object):
    def __init__(self, request, context, reference: Reference):
        self.context = context
        self.request = request
        self.ref = reference
        self.title = reference.get_title(request)

    def resolve(self):
        value = self.context[self.ref.name]
        collection = self.ref.collection(self.request)
        items = collection.search(rulez.field(self.ref.attribute) == value)
        if items:
            return items[0]
        return None


class BackReference(object):
    def __init__(
        self,
        name: str,
        resource_type: str,
        reference_name: str,
        *,
        title=None,
        single=False,
        metadata=None,
    ):
        self.name = name
        self.resource_type = resource_type
        self.reference_name = reference_name
        self.title = title
        self.single_reference = single
        self.metadata = metadata or {}

    def collection(self, request):
        return request.get_collection(self.resource_type)

    def get_title(self, request):
        typeinfo = request.get_typeinfo(self.resource_type)
        return self.title or typeinfo["title"]

    def get_reference(self, request):
        typeinfo = request.app.config.type_registry.get_typeinfo(
            name=self.resource_type, request=request
        )
        refschema = typeinfo["schema"]
        for ref in refschema.__references__:
            if ref.name == self.reference_name:
                return ref


class BackReferenceResolver(object):
    def __init__(self, request, context, backreference: BackReference):
        self.context = context
        self.request = request
        self.bref = backreference
        self.title = backreference.get_title(request)

    def resolve(self):
        request = self.request
        context = self.context

        reference = self.bref.get_reference(request)

        if reference is None:
            raise ValueError("Invalid reference name. %s" % self.bref.reference_name)

        value = context[reference.attribute]
        collection = self.bref.collection(request)
        items = collection.search(rulez.field(reference.name) == value)
        return items

