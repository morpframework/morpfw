import reg
from reg.dispatch import Dispatch, validate_signature
from reg.context import DispatchMethod
from reg.predicate import PredicateRegistry
from functools import partial


def _dispatch_subscribe(self, func=None, **key_dict):
    if func is None:
        return partial(self.subscribe, **key_dict)
    validate_signature(func, self.wrapped_func)
    predicate_key = self.registry.key_dict_to_predicate_key(key_dict)
    self.registry.subscribe(predicate_key, func)
    return func


def _dispatch_publish(self, *args, **kwargs):
    subscribers = self.by_args(*args, **kwargs).all_matches
    return list([sub(*args, **kwargs) for sub in subscribers])


def _dispatchmethod_publish(self, app, *args, **kwargs):
    subscribers = self.by_args(*args, **kwargs).all_matches
    return list([sub(app, *args, **kwargs) for sub in subscribers])


def _registry_subscribe(self, key, value):
    for index, key_item in zip(self.indexes, key):
        index.setdefault(key_item, set()).add(value)


if not getattr(PredicateRegistry, '__pubsub_patched', False):
    PredicateRegistry.subscribe = _registry_subscribe
    PredicateRegistry.__pubsub_patched = True


if not getattr(Dispatch, '__pubsub_patched', False):
    Dispatch.subscribe = _dispatch_subscribe
    Dispatch.publish = _dispatch_publish
    Dispatch.__pubsub_patched = True

if not getattr(DispatchMethod, '__pubsub_dispatchmethod_patched', False):
    DispatchMethod.publish = _dispatchmethod_publish
    DispatchMethod.__pubsub_dispatchmethod_patched = True
