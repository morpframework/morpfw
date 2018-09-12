import copy


class BaseStorage(object):

    use_transactions = True

    @property
    def model(self):
        raise NotImplementedError

    def __init__(self, request):
        self.request = request
        self.app = request.app

    def set_identifier(self, obj, identifier):
        for f, v in zip(
                self.app.get_jslcrud_identifierfields(self.model.schema),
                identifier.split(
                    self.app.get_jslcrud_compositekey_separator())):
            obj[f] = v

    def set_schema_defaults(self, data):
        data = copy.deepcopy(data)
        for fieldname, field in self.model.schema._fields.items():
            if field.required and fieldname not in data.keys():
                data[fieldname] = field.get_default()
        return data

    def create(self, data):
        raise NotImplementedError

    def search(self, query=None, limit=None):
        raise NotImplementedError

    def get(self, identifier):
        raise NotImplementedError

    def get_by_uuid(self, uuid):
        raise NotImplementedError

    def update(self, identifier, data):
        raise NotImplementedError

    def delete(self, identifier, model):
        raise NotImplementedError
