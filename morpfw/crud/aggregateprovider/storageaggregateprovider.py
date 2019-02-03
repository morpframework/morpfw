from .base import AggregateProvider
from ..model import Collection
from ..app import App


class StorageAggregateProvider(AggregateProvider):

    def aggregate(self, query=None, group=None, order_by=None):
        return self.storage.aggregate(query, group=group, order_by=order_by)


@App.aggregateprovider(model=Collection)
def get_aggregateprovider(context):
    return StorageAggregateProvider(context)
