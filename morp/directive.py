import dectate
import reg
import celery
from uuid import uuid4


class CeleryTaskAction(dectate.Action):

    app_class_arg = True

    def __init__(self, name):
        self.name = name

    def identifier(self, app_class):
        return str((app_class, self.name))

    def perform(self, obj, app_class):

        task = app_class.celery.task(obj)
        app_class.celery_task.register(
            reg.methodify(lambda name: task), name=self.name)


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


class CeleryMetastoreAction(dectate.Action):

    app_class_arg = True

    def __init__(self, metastore, schema):
        self.metastore = metastore
        self.schema = schema

    def identifier(self, app_class):
        return str((app_class, self.metastore, self.schema))

    def perform(self, obj, app_class):

        app_class._get_celery_metastore.register(
            reg.methodify(obj), metastore=self.metastore, schema=self.schema)
