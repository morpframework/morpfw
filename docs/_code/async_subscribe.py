import morpfw
import time
import pytest


# lets setup a skeleton app

class App(morpfw.BaseApp):
    pass


class Root(object):
    pass


@App.path(model=Root, path='')
def get_root(request):
    return Root()


# this view will dispatch the event

@App.json(model=Root)
def index(context, request):
    subs = request.app.async_dispatcher(
        'test_signal').dispatch(request, obj={'data': 10})
    res = []
    for s in subs:
        res.append(s.get())
    return res


# these are the async handlers

@App.async_subscribe('test_signal')
def handler1(request, obj):
    obj['handler'] = 'handler1'
    obj['data'] += 1
    return obj


@App.async_subscribe('test_signal')
def handler2(request, obj):
    obj['handler'] = 'handler2'
    obj['data'] += 5
    return obj
