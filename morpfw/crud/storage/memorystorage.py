from morepath.request import Request
from rulez import compile_condition
from .base import BaseStorage
import jsl

DATA = {}


class MemoryStorage(BaseStorage):

    incremental_id = False
    incremental_column = 'id'

    @property
    def datastore(self):
        return DATA[self.typekey]

    @property
    def typekey(self):
        return ':'.join([self.__module__, self.__class__.__name__])

    def __init__(self, request, blobstorage=None):
        DATA.setdefault(self.typekey, {})
        super(MemoryStorage, self).__init__(request, blobstorage)

    def create(self, data):
        data = data.copy()
        obj = self.model(self.request, self, data)
        if self.incremental_id:
            obj.data[self.incremental_column] = len(DATA[self.typekey]) + 1
        identifier = obj.identifier
        DATA[self.typekey][identifier] = obj
        return obj

    def aggregate(self, query=None, group=None, order_by=None):
        raise NotImplementedError

    def search(self, query=None, offset=None, limit=None, order_by=None):
        res = []
        if query:
            f = compile_condition('native', query)
            for o in DATA[self.typekey].values():
                if f(o.data):
                    res.append(o)
        else:
            res = list(DATA[self.typekey].values())
        for r in res:
            r.request = self.request
        if offset is not None:
            res = res[offset:]
        if limit is not None:
            res = res[:limit]
        if order_by is not None:
            col, d = order_by
            res = list(sorted(res, key=lambda x: x.data[col]))
            if d == 'desc':
                res = list(reversed(res))
        return res

    def get(self, identifier):
        if identifier not in DATA[self.typekey].keys():
            return None
        res = DATA[self.typekey][identifier]
        res.request = self.request
        return res

    def get_by_id(self, id):
        id_field = self.incremental_column
        data_by_id = {}
        for u, v in DATA[self.typekey].items():
            if id_field not in v.data.keys():
                raise AttributeError(
                    '%s does not have %s field' % (v, id_field))
            data_by_id[v.data[id_field]] = v

        if id not in data_by_id.keys():
            return None
        res = data_by_id[id]
        res.request = self.request
        return res

    def get_by_uuid(self, uuid):
        uuid_field = self.app.get_uuidfield(self.model.schema)
        data_by_uuid = {}
        for u, v in DATA[self.typekey].items():
            if uuid_field not in v.data.keys():
                raise AttributeError(
                    '%s does not have %s field' % (v, uuid_field))
            data_by_uuid[v.data[uuid_field]] = v

        if uuid not in data_by_uuid.keys():
            return None
        res = data_by_uuid[uuid]
        res.request = self.request
        return res

    def update(self, identifier, data):
        obj = DATA[self.typekey][identifier]
        for k, v in data.items():
            obj.data[k] = v
        return obj

    def delete(self, identifier, model):
        del DATA[self.typekey][identifier]
