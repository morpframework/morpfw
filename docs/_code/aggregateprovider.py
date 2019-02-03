import typing
import morpfw
from .app import App
from .model import PageCollection


class PagesAggregateProvider(morpfw.AggregateProvider):

    def aggregate(self, query=None, group=None, order_by=None):
        """search for resources, aggregate and return aggregate result"""
        result = []
        # do something here
        return result


@App.aggregateprovider(model=PageCollection)
def get_aggregateprovider(context):
    return PagesAggregateProvider(context)
