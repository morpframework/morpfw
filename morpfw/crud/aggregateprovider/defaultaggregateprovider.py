from ..model import Collection
from ..errors import UnprocessableError
from ..app import App
import re


class AggregateProvider(object):

    pattern = re.compile(r'(\w+):(\w+)\((\w+)\)')

    def __init__(self, context: Collection):
        self.context = context
        self.storage = context.storage
        self.request = context.request

    def _parse(self, qs):
        tokens = [ss.strip() for ss in qs.strip().split(',')]
        result = []
        for t in tokens:
            m = self.pattern.match(t)
            if not m:
                raise ValueError(t)
            g = m.groups()
            result.append((g[0], {'function': g[1], 'field': g[2]}))
        return dict(result)

    def parse_group(self, qs):
        if not qs.strip():
            return None
        try:
            return self._parse(qs)
        except ValueError:
            raise UnprocessableError("Invalid aggregate query '%s'" % qs)
        return None

    def aggregate(self, query=None, group=None, order_by=None):
        return self.storage.aggregate(query, group=group, order_by=order_by)


@App.aggregateprovider(model=Collection)
def get_aggregateprovider(context):
    return AggregateProvider(context)
