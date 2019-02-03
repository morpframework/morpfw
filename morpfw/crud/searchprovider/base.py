from ..errors import UnprocessableError
from ..model import Collection
from ...interfaces import ISearchProvider
from rulez import parse_dsl, OperatorNotAllowedError


class SearchProvider(ISearchProvider):

    def __init__(self, context: Collection):
        self.context = context
        self.storage = context.storage
        self.request = context.request

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
