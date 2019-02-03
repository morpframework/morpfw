from ..app import App
from ..model import Model


class RulesProvider(object):

    def __init__(self, context: Model):
        self.context = context
        self.request = context.request
        self.app = context.app

    @property
    def schema(self):
        return self.context.schema

    @property
    def identifier(self):
        return self.context.identifier

    @property
    def data(self):
        return self.context.data

    def json(self):
        return self.context.json()

    def update(self, *args, **kwargs):
        return self.context.update(*args, **kwargs)

    def delete(self):
        return self.context.delete()

    def links(self):
        return []


@App.rulesprovider(model=Model)
def get_default_rulesprovider(context):
    return RulesProvider(context)
