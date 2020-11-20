import time

import morpfw
import pytest

# lets setup a skeleton app


class App(morpfw.BaseApp):
    pass


class Root(object):
    pass


@App.path(model=Root, path="")
def get_root(request):
    return Root()


# this view will dispatch the event


@App.json(model=Root)
def index(context, request):
    subs = request.async_dispatch("test_signal", obj={"data": 10})
    res = []
    for s in subs:
        res.append(s.get())
    return res


# these are the async handlers


@App.async_subscribe("test_signal")
def handler1(request_options, obj):
    # request_options contain parameters for instantiating a request
    with morpfw.request_factory(**request_options) as request:
        obj["handler"] = "handler1"
        obj["data"] += 1
        return obj


@App.async_subscribe("test_signal")
def handler2(request_options, obj):
    with morpfw.request_factory(**request_options) as request:
        obj["handler"] = "handler2"
        obj["data"] += 5
        return obj
