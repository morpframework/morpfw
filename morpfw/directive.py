import dectate
import reg
import celery
from uuid import uuid4


class CelerySubscriberAction(dectate.Action):

    app_class_arg = True

    config = {
        'celery_subscriber_registry': dict
    }

    def __init__(self, signal):
        self.signal = signal

    def identifier(self, celery_subscriber_registry, app_class):
        return str((app_class, uuid4().hex, self.signal))

    def perform(self, obj, celery_subscriber_registry, app_class):
        celery_subscriber_registry.setdefault(self.signal, [])
        celery_subscriber_registry[self.signal].append(obj)
