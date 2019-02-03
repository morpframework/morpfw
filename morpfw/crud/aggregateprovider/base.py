from ..model import Collection
from ..errors import UnprocessableError
from ...interfaces import IAggregateProvider
import re
from rulez import parse_dsl, OperatorNotAllowedError


class AggregateProvider(IAggregateProvider):

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

    def parse_query(self, qs):
        if not qs.strip():
            return None
        try:
            return parse_dsl(qs)
        except ValueError:
            raise UnprocessableError("Invalid search query '%s'" % qs)
        except OperatorNotAllowedError:
            raise UnprocessableError("Invalid search query '%s'" % qs)
        return None

    def parse_group(self, qs):
        if not qs.strip():
            return None
        try:
            return self._parse(qs)
        except ValueError:
            raise UnprocessableError("Invalid aggregate query '%s'" % qs)
        return None
