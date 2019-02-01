from ..errors import UnprocessableError
from ..model import Collection
from ..app import App
from rulez import parse_dsl, OperatorNotAllowedError


class SearchProvider(object):

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

    def search(self, query=None, offset=0, limit=None, order_by=None):
        return self.storage.search(query, offset, limit, order_by)


@App.searchprovider(model=Collection)
def get_searchprovider(context):
    return SearchProvider(context)
