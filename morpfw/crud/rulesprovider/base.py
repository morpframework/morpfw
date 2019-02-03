from ..model import Model


class RulesProvider(object):

    def __init__(self, context: Model):
        self.context = context
        self.request = context.request
        self.app = context.app
