import inspect
from uuid import uuid4

import dectate
import reg

from . import pubsub

OBJECT_CREATED = "morpfw.object_created"
OBJECT_UPDATED = "morpfw.object_updated"
OBJECT_TOBEDELETED = "morpfw.object_tobedeleted"


def _get_identifier(obj):
    if inspect.isclass(obj):
        return [obj.__module__, obj.__name__]
    if getattr(obj, "__class__", None):
        return [obj.__module__, obj.__class__.__name__]
    raise ValueError("%s is neither instance nor class" % obj)


def construct_key(signal, app, obj):
    return ":".join([signal] + _get_identifier(obj))


class Connect(dectate.Action):

    app_class_arg = True

    def __init__(self, model, signal):
        self.model = model
        self.signal = signal

    def identifier(self, app_class):
        return uuid4().hex

    def perform(self, obj, app_class):
        app_class._events.subscribe(obj, model=self.model, signal=self.signal)


class Dispatcher(object):
    def __init__(self, app, signal):
        self.app = app
        self.signal = signal

    def dispatch(self, request, context):
        self.app._events.publish(self.app, request, context, self.signal)


class SignalApp(dectate.App):

    subscribe = dectate.directive(Connect)

    @reg.dispatch_method(
        reg.match_instance("model", lambda self, request, obj, signal: obj),
        reg.match_key("signal", lambda self, request, obj, signal: signal),
    )
    def _events(self, request, obj, signal):
        raise NotImplementedError

    def dispatcher(self, signal):
        return Dispatcher(self, signal)
