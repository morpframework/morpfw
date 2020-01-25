from ..model import Collection
from ..app import App
from .base import SearchProvider


class StorageSearchProvider(SearchProvider):
    def search(self, query=None, offset=0, limit=None, order_by=None):
        return self.storage.search(self.context, query, offset, limit, order_by)


@App.searchprovider(model=Collection)
def get_searchprovider(context):
    return StorageSearchProvider(context)
