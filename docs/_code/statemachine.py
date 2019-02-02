import typing
from dataclasses import dataclass
import morpfw
from .app import App
from .model import PageModel


class PageStateMachine(morpfw.StateMachine):

    states = ['new', 'pending', 'approved']
    transitions = [
        {'trigger': 'approve', 'source': [
            'new', 'pending'], 'dest': 'approved'},
        {'trigger': 'submit', 'source': 'new', 'dest': 'pending'}
    ]


@App.statemachine(model=PageModel)
def get_pagemodel_statemachine(context):
    return PageStateMachine(context)
