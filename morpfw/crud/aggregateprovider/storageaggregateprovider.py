from ..app import App
from ..model import Collection
from .base import AggregateProvider


class StorageAggregateProvider(AggregateProvider):
    def aggregate(self, query=None, group=None, order_by=None, limit=None):
        return self.storage.aggregate(
            query, group=group, order_by=order_by, limit=limit
        )


@App.aggregateprovider(model=Collection)
def get_aggregateprovider(context):
    return StorageAggregateProvider(context)
