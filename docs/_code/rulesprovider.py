import typing
import morpfw
from .app import App
from .model import PageModel


class PageRulesProvider(morpfw.RulesProvider):

    def calculate_value_offset(self):
        return self.context['value'] + 1


@App.rulesprovider(model=PageModel)
def get_rulesprovider(context):
    return PageRulesProvider(context)


@App.json(model=PageModel, name='get-value-offset')
def get_value_offset(context, request):
    return context.rulesprovider().calculate_value_offset()
