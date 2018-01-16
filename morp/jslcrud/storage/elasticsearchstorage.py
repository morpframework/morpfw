from ..errors import NotFoundError
from .base import BaseStorage
from rulez import compile_condition
import elasticsearch.exceptions as es_exc
from ..app import App


class ElasticSearchStorage(BaseStorage):

    refresh = False
    auto_id = False
    use_transactions = False

    @property
    def index_name(self):
        raise NotImplementedError

    @property
    def doc_type(self):
        raise NotImplementedError

    @property
    def client(self):
        return self.request.es_client

    def create_index(self):
        if not self.client.indices.exists(self.index_name):
            try:
                self.client.indices.create(index=self.index_name, body={
                    'settings': {
                        'number_of_shards': 1,
                        'number_of_replicas': 0
                    }
                })
            except es_exc.TransportError as e:
                if e.error == 'index_already_exists_exception':
                    return
                raise e

    def create(self, data):
        m = self.model(self.request, self, data)
        self.create_index()
        try:
            r = self.client.index(index=self.index_name,
                                  doc_type=self.doc_type,
                                  id=m.identifier,
                                  body=data, refresh=self.refresh)
        except es_exc.TransportError as e:
            print(e.args, e.error, e.info)
            print(data)
            raise e

        if self.auto_id:
            self.set_identifier(m.data, r['_id'])
            m.save()
        return m

    def search(self, query=None, offset=None, limit=None, order_by=None):
        if query:
            q = {'query': compile_condition('elasticsearch', query)()}
        else:
            q = {'query': {'match_all': {}}}
        if limit is not None:
            q['from'] = 0
            q['size'] = limit

        self.create_index()
        params = {}
        if offset is not None:
            params['from_'] = offset
        if limit:
            params['size'] = limit
        if order_by:
            params['sort'] = [':'.join(order_by)]
        res = self.client.search(index=self.index_name, doc_type=self.doc_type,
                                 body=q, **params)

        data = [self.model(self.request, self, o['_source'])
                for o in res['hits']['hits']]

        return list(data)

    def get(self, identifier):
        self.create_index()
        try:
            res = self.client.get(index=self.index_name,
                                  doc_type=self.doc_type, id=identifier,
                                  refresh=self.refresh)
        except es_exc.NotFoundError as e:
            raise NotFoundError(self.model, identifier)
        return self.model(self.request, self, res['_source'])

    def get_by_uuid(self, uuid):
        res = self.search({'field': 'uuid', 'operator': '==', 'value': uuid})
        if res:
            return self.model(self.request, self, res[0].json()['data'])
        raise NotFoundError(self.model, uuid)

    def update(self, identifier, data):
        self.create_index()
        self.client.update(index=self.index_name, doc_type=self.doc_type,
                           id=identifier, body={'doc': data},
                           refresh=self.refresh)

    def delete(self, identifier):
        self.create_index()
        self.client.delete(index=self.index_name, doc_type=self.doc_type,
                           id=identifier, refresh=True)
