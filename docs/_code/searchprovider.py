import typing
import morpfw
from .app import App
from .model import PageCollection


class PagesSearchProvider(morpfw.SearchProvider):

    def search(self, query=None, offset=0, limit=None, order_by=None):
        """search for resources and return list of resource model objects"""
        result = []
        # do something here
        return result


@App.searchprovider(model=PageCollection)
def get_searchprovider(context):
    return PagesSearchProvider(context)
