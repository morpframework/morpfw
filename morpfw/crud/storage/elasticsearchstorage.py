import copy
import json
from pprint import pprint
from typing import Optional

import elasticsearch.exceptions as es_exc
from inverter import dc2colanderESjson, dc2esmapping
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

        if not self.groups:
            self._finalized = True
            return

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
        if not self.groups:
            return {}
        return self.groups[0].json()

    def parse(self, result):
        if not self._finalized:
            self.finalize()
        return self.groups[0].parse(result)


def is_text_mapping(collection, field):
    schema = collection.schema
    f = schema.__dataclass_fields__[field]
    fmt = f.metadata.get("format", None)
    if not fmt:
        return False

    if fmt.startswith("text"):
        return True
    return False


class ElasticSearchStorage(BaseStorage):

    refresh: Optional[str] = None
    auto_id = False
    use_transactions = False

    @property
    def index_name(self):
        raise NotImplementedError

    @property
    def client(self):
        return self.request.get_es_client()

    def create_index(self, collection, recreate=False):
        if self.client.indices.exists(self.index_name) and recreate == False:
            return False

        if recreate == True:
            self.client.indices.delete(self.index_name)

        settings = self.request.app.get_config(
            "morpfw.storage.elasticsearch.index_settings.%s" % self.index_name, None,
        )
        body = {}
        if settings:
            body["settings"] = settings or {
                "number_of_shards": 1,
                "number_of_replicas": 0,
            }

        mapping = dc2esmapping.convert(collection.schema)
        body.update(mapping)
        self.client.indices.create(
            index=self.index_name, body=body,
        )

        return True

    def update_index(self, collection):
        if not self.client.indices.exists(self.index_name):
            return False

        fields = list(collection.schema.__dataclass_fields__.keys())
        mappings = self.client.indices.get_field_mapping(
            fields, index=self.index_name, ignore_unavailable=True
        )

        existing_fields = list(mappings[self.index_name]["mappings"].keys())
        new_fields = [x for x in fields if x not in existing_fields]
        new_mapping = dc2esmapping.convert(
            collection.schema, include_fields=list(new_fields)
        )
        self.client.indices.put_mapping(
            index=self.index_name, body=new_mapping["mappings"],
        )
        return True

    def create(self, collection, data):
        m = self.model(self.request, collection, data)
        cschema = dc2colanderESjson.convert(
            collection.schema,
            request=collection.request,
            default_tzinfo=collection.request.timezone(),
        )
        esdata = cschema().serialize(data)
        try:
            r = self.client.index(
                index=self.index_name,
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

        params = {}
        if offset is not None:
            params["from_"] = offset
        if limit:
            params["size"] = limit
        if order_by:
            if is_text_mapping(collection, order_by[0]):
                params["sort"] = [":".join(["%s.raw" % order_by[0], order_by[1]])]
            else:
                params["sort"] = [":".join(order_by)]

        res = self.client.search(index=self.index_name, body=q, **params)

        models = []
        for o in res["hits"]["hits"]:
            data = o["_source"]
            cschema = dc2colanderESjson.convert(
                collection.schema,
                include_fields=data.keys(),
                request=collection.request,
                default_tzinfo=collection.request.timezone(),
            )
            data = cschema().deserialize(data)
            models.append(self.model(self.request, collection, data))

        return list(models)

    def aggregate(self, query=None, group=None, order_by=None, limit=None):
        if group is None:
            return []

        if query:
            q = {"query": compile_condition("elasticsearch", query)()}
        else:
            q = {"query": {"match_all": {}}}

        q["size"] = 0

        params = {}
        if order_by:
            params["sort"] = [":".join(order_by)]
        if limit is not None:
            params["size"] = limit

        aggs = {}
        sources = []
        result_converters = {}
        if group:

            for k, v in group.items():
                if isinstance(v, str):
                    sources.append({k: {"terms": {"field": v}}})

                elif isinstance(v, dict):
                    ff = v["function"]
                    f = v["field"]
                    if ff == "count":
                        aggs[k] = {"value_count": {"field": f}}
                    elif ff == "sum":
                        aggs[k] = {"sum": {"field": f}}
                    elif ff == "avg":
                        aggs[k] = {"avg": {"field": f}}
                    elif ff == "year":
                        sources.append(
                            {
                                k: {
                                    "date_histogram": {
                                        "field": f,
                                        "interval": "year",
                                        "format": "yyyy",
                                    }
                                }
                            }
                        )
                        result_converters[k] = lambda request, value: int(value)

                    elif ff == "month":
                        sources.append(
                            {
                                k: {
                                    "date_histogram": {
                                        "field": f,
                                        "interval": "month",
                                        "format": "MM",
                                    }
                                }
                            }
                        )

                        result_converters[k] = lambda request, value: int(value)

                    elif ff == "day":
                        sources.append(
                            {
                                k: {
                                    "date_histogram": {
                                        "field": f,
                                        "interval": "day",
                                        "format": "dd",
                                    }
                                }
                            }
                        )

                        result_converters[k] = lambda request, value: int(value)

                    elif ff == "interval_1m":
                        sources.append(
                            {
                                k: {
                                    "date_histogram": {
                                        "field": f,
                                        "interval": "1m",
                                        "format": "yyyy-MM-dd'T'HH:mmZ",
                                    }
                                }
                            }
                        )

                    elif ff == "interval_15m":
                        sources.append(
                            {
                                k: {
                                    "date_histogram": {
                                        "field": f,
                                        "interval": "15m",
                                        "format": "yyyy-MM-dd'T'HH:mmZ",
                                    }
                                }
                            }
                        )
                    elif ff == "interval_30m":
                        sources.append(
                            {
                                k: {
                                    "date_histogram": {
                                        "field": f,
                                        "interval": "30m",
                                        "format": "yyyy-MM-dd'T'HH:mmZ",
                                    }
                                }
                            }
                        )

                    elif ff == "interval_1h":
                        sources.append(
                            {
                                k: {
                                    "date_histogram": {
                                        "field": f,
                                        "interval": "1h",
                                        "format": "yyyy-MM-dd'T'HH:mmZ",
                                    }
                                }
                            }
                        )

                    else:
                        raise ValueError("Unknown function %s" % ff)

            if sources:
                q["aggs"] = {
                    "results": {"composite": {"sources": sources}, "aggs": aggs}
                }
                if limit is not None:
                    q["aggs"]["results"]["composite"]["size"] = limit
            else:
                q["aggs"] = aggs

        res = self.client.search(index=self.index_name, body=q, **params)

        if "aggregations" not in res:
            if len(group) == 1 and "count" in group.keys():
                return [{"count": res["hits"]["total"]["value"]}]
            raise AssertionError(
                "Unsupported query\n  Query: %s\n  Result: %s"
                % (json.dumps(q, indent=4), json.dumps(res, indent=4))
            )

        result = []
        if sources:
            data = res["aggregations"]["results"]["buckets"]
            for row in data:
                r = row["key"].copy()
                for k in aggs:
                    r[k] = row[k]["value"]
                for k, f in result_converters.items():
                    r[k] = f(self.request, r[k])
                result.append(r)
            return result

        data = res["aggregations"]
        r = {}
        for k in aggs:
            r[k] = data[k]["value"]
        return [r]

    def get(self, collection, identifier):
        try:
            res = self.client.get(
                index=self.index_name, id=identifier, refresh=self.refresh,
            )
        except es_exc.NotFoundError as e:
            return None

        data = res["_source"]
        cschema = dc2colanderESjson.convert(
            collection.schema,
            include_fields=data.keys(),
            request=collection.request,
            default_tzinfo=collection.request.timezone(),
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
        res = self.client.get(index=self.index_name, id=id)
        data = res["_source"]
        cschema = dc2colanderESjson.convert(
            collection.schema,
            include_fields=data.keys(),
            request=collection.request,
            default_tzinfo=collection.request.timezone(),
        )
        data = cschema().deserialize(data)
        return self.model(self.request, collection, data)

    def update(self, collection, identifier, data):
        cschema = dc2colanderESjson.convert(
            collection.schema,
            include_fields=data.keys(),
            request=collection.request,
            default_tzinfo=collection.request.timezone(),
        )
        data = cschema().serialize(data)
        self.client.update(
            index=self.index_name,
            id=identifier,
            body={"doc": data},
            refresh=self.refresh,
        )

    def delete(self, identifier, model, **kwargs):
        self.client.delete(index=self.index_name, id=identifier, refresh=True)

