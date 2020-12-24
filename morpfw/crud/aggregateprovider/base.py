import re

from rulez import OperatorNotAllowedError, parse_dsl

from ...interfaces import IAggregateProvider
from ..errors import UnprocessableError
from ..model import Collection


class AggregateProvider(IAggregateProvider):

    field_pattern = re.compile(r"(\w+):(\w+)")
    function_pattern = re.compile(r"(\w+):([\_\w]+)\((\w+)\)")

    def __init__(self, context: Collection):
        self.context = context
        self.storage = context.storage
        self.request = context.request

    def _parse(self, qs):
        tokens = [ss.strip() for ss in qs.strip().split(",")]
        result = []
        for t in tokens:
            m = self.function_pattern.match(t)
            if m:
                g = m.groups()
                result.append((g[0], {"function": g[1], "field": g[2]}))
                continue
            m = self.field_pattern.match(t)
            if m:
                f, v = t.split(":")
                result.append((f, v))
                continue
            raise ValueError(t)

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
