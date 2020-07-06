import copy
from pprint import pprint
from typing import Optional

import elasticsearch.exceptions as es_exc
from inverter import dc2colanderESjson
from rulez import compile_condition

from ..app import App
from .base import BaseStorage


class AggGroup(object):
    def __init__(self, key, field, type="terms", opts=None, children=None):
        self.key = key
        self.field = field
        self.type = type
        self.children = children or []
        self.parent = None
        self.is_leaf = False
        self.opts = opts or {}

    def parse(self, result, parents=None):
        parents = parents or {}
        records = result[self.key]["buckets"]
        results = []
        for r in records:
            key = r["key_as_string"]
            if self.type == "date_histogram":
                if self.opts.get("format", None) in ["yyyy", "MM", "dd"]:
                    key = int(key)
            parents[self.key] = key
            if self.is_leaf:
                values = copy.copy(parents)
                for c in self.children:
                    if c.function == "count":
                        values[c.key] = r["doc_count"]
                    else:
                        values.update(c.parse(r, parents=parents))
                results.append(values)
            else:
                values = []
                for c in self.children:
                    values += c.parse(r, parents=parents)
                results += values
        return results

    def json(self):
        res = {self.type: {"field": self.field}}

        if self.opts:
            res[self.type].update(self.opts)

        if self.children:
            for c in self.children:
                res.setdefault("aggs", {})
                res["aggs"].update(c.json())

        return {self.key: res}


class AggValue(object):
    def __init__(self, key, function, field):
        self.key = key
        self.function = function
        self.field = field
        self.parent = None

    def parse(self, result, parents=None):
        if self.function == "count":
            return {}
        parents = parents or {}
        p = copy.copy(parents)
        p[self.key] = result[self.key][self.field]
        return p

    def json(self):
        if self.function == "count":
            return {}
        return {self.key: {self.function: {"field": self.field}}}


class Aggregate(object):
    def __init__(self):
        self.groups = []
        self.values = []
        self.first_group = None
        self._finalized = False

    def add_group(self, key, field, type="terms", opts=None):
        if self._finalized:
            raise ValueError("Aggregate has been finalized")
        self.groups.append(AggGroup(key, field, type, opts))

    def add(self, key, function, field):
        if self._finalized:
            raise ValueError("Aggregate has been finalized")
        self.values.append(AggValue(key, function, field))

    def finalize(self):
        if self._finalized:
            raise ValueError("Aggregate has been finalized")

        prev = None
        first = None
        for g in self.groups:
            if prev is None:
                prev = g
                continue
            if g not in prev.children:
                prev.children.append(g)
                g.parent = prev
            prev = g
        prev.is_leaf = True
        for v in self.values:
            if v not in prev.children:
                prev.children.append(v)
                v.parent = prev

        self._finalized = True

    def json(self):
        if not self._finalized:
            self.finalize()
        return self.groups[0].json()

    def parse(self, result):
        if not self._finalized:
            self.finalize()
        return self.groups[0].parse(result)


class ElasticSearchStorage(BaseStorage):

    refresh: Optional[str] = None
    auto_id = False
    use_transactions = False
    doc_type = "_doc"

    @property
    def index_name(self):
        raise NotImplementedError

    @property
    def client(self):
        return self.request.es_client

    def create_index(self):
        if not self.client.indices.exists(self.index_name):
            try:
                self.client.indices.create(
                    index=self.index_name,
                    body={"settings": {"number_of_shards": 1, "number_of_replicas": 0}},
                )
            except es_exc.TransportError as e:
                if e.error == "index_already_exists_exception":
                    return
                raise e

    def create(self, collection, data):
        m = self.model(self.request, collection, data)
        cschema = dc2colanderESjson.convert(
            collection.schema, request=collection.request
        )
        esdata = cschema().serialize(data)
        self.create_index()
        try:
            r = self.client.index(
                index=self.index_name,
                doc_type=self.doc_type,
                id=m.identifier,
                body=esdata,
                refresh=self.refresh,
            )
        except es_exc.TransportError as e:
            print(e.args, e.error, e.info)
            print(data)
            raise e

        if self.auto_id:
            self.set_identifier(m.data, r["_id"])
            m.save()
        return m

    def search(self, collection, query=None, offset=None, limit=None, order_by=None):
        if limit is None:
            limit = 9999
        if query:
            q = {"query": compile_condition("elasticsearch", query)()}
        else:
            q = {"query": {"match_all": {}}}
        if limit is not None:
            q["from"] = 0
            q["size"] = limit

        self.create_index()
        params = {}
        if offset is not None:
            params["from_"] = offset
        if limit:
            params["size"] = limit
        if order_by:
            params["sort"] = [":".join(order_by)]
        res = self.client.search(
            index=self.index_name, doc_type=self.doc_type, body=q, **params
        )

        models = []
        for o in res["hits"]["hits"]:
            data = o["_source"]
            cschema = dc2colanderESjson.convert(
                collection.schema,
                include_fields=data.keys(),
                request=collection.request,
            )
            data = cschema().deserialize(data)
            models.append(self.model(self.request, collection, data))

        return list(models)

    def aggregate(self, query=None, group=None, order_by=None):
        if query:
            q = {"query": compile_condition("elasticsearch", query)()}
        else:
            q = {"query": {"match_all": {}}}

        q["size"] = 0

        self.create_index()
        params = {}
        if order_by:
            params["sort"] = [":".join(order_by)]

        if group:
            aggs = Aggregate()

            for k, v in group.items():
                if isinstance(v, str):
                    aggs.add_group(k, v)

                elif isinstance(v, dict):
                    ff = v["function"]
                    f = v["field"]
                    if ff == "count":
                        aggs.add(k, "count", f)
                    elif ff == "sum":
                        aggs.add(k, "sum", f)
                    elif ff == "avg":
                        aggs.add(k, "avg", f)
                    elif ff == "year":
                        aggs.add_group(
                            k,
                            f,
                            type="date_histogram",
                            opts={"interval": "year", "format": "yyyy"},
                        )
                    elif ff == "month":
                        aggs.add_group(
                            k,
                            f,
                            type="date_histogram",
                            opts={"interval": "month", "format": "MM"},
                        )
                    elif ff == "day":
                        aggs.add_group(
                            k,
                            f,
                            type="date_histogram",
                            opts={"interval": "day", "format": "dd"},
                        )
                    elif ff == "interval-1m":
                        aggs.add_group(
                            k,
                            f,
                            type="date_histogram",
                            opts={"interval": "1m", "format": "yyyy-MM-dd'T'HH:mm"},
                        )
                    elif ff == "interval-15m":
                        aggs.add_group(
                            k,
                            f,
                            type="date_histogram",
                            opts={"interval": "15m", "format": "yyyy-MM-dd'T'HH:mm"},
                        )
                    elif ff == "interval-30m":
                        aggs.add_group(
                            k,
                            f,
                            type="date_histogram",
                            opts={"interval": "30m", "format": "yyyy-MM-dd'T'HH:mm"},
                        )
                    elif ff == "interval-1h":
                        aggs.add_group(
                            k,
                            f,
                            type="date_histogram",
                            opts={"interval": "1h", "format": "yyyy-MM-dd'T'HH:mm"},
                        )
                    else:
                        raise ValueError("Unknown function %s" % ff)

            aggs.finalize()
            q["aggs"] = aggs.json()
        res = self.client.search(
            index=self.index_name, doc_type=self.doc_type, body=q, **params
        )
        data = aggs.parse(res["aggregations"])

        return list(data)

    def get(self, collection, identifier):
        self.create_index()
        try:
            res = self.client.get(
                index=self.index_name,
                doc_type=self.doc_type,
                id=identifier,
                refresh=self.refresh,
            )
        except es_exc.NotFoundError as e:
            return None

        data = res["_source"]
        cschema = dc2colanderESjson.convert(
            collection.schema, include_fields=data.keys(), request=collection.request,
        )
        data = cschema().deserialize(data)
        return self.model(self.request, collection, data)

    def get_by_uuid(self, collection, uuid):
        res = self.search(
            collection, {"field": "uuid", "operator": "==", "value": uuid}
        )
        if res:
            data = res[0].as_dict()
            return self.model(self.request, collection, data)
        return None

    def get_by_id(self, collection, id):
        res = self.client.get(index=self.index_name, doc_type=self.doc_type, id=id)
        data = res["_source"]
        cschema = dc2colanderESjson.convert(
            collection.schema, include_fields=data.keys(), request=collection.request,
        )
        data = cschema().deserialize(data)
        return self.model(self.request, collection, data)

    def update(self, collection, identifier, data):
        cschema = dc2colanderESjson.convert(
            collection.schema, include_fields=data.keys(), request=collection.request
        )
        data = cschema().serialize(data)
        self.create_index()
        self.client.update(
            index=self.index_name,
            doc_type=self.doc_type,
            id=identifier,
            body={"doc": data},
            refresh=self.refresh,
        )

    def delete(self, identifier, model, **kwargs):
        self.create_index()
        self.client.delete(
            index=self.index_name, doc_type=self.doc_type, id=identifier, refresh=True
        )
