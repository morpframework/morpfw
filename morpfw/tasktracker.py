import jsl
from . import jslcrud
from .jslcrud.storage.sqlstorage import Base
import sqlalchemy as sa
import sqlalchemy_jsonfield as sajson
from .app import BaseApp
from .jslcrud.storage.memorystorage import MemoryStorage
from .jslcrud.storage.sqlstorage import SQLStorage
import json
from celery.result import AsyncResult
import transaction
import time
import rulez


class CeleryTaskSchema(jsl.Document):
    task = jsl.StringField()
    task_id = jsl.StringField()
    created_ts = jsl.IntField()
    status = jsl.StringField()
    input = jsl.DictField()
    result = jsl.DictField()
    traceback = jsl.StringField()


@BaseApp.jslcrud_identifierfields(schema=CeleryTaskSchema)
def task_identifierfields(schema):
    return ['task_id']


class CeleryTask(Base):
    __tablename__ = 'celery_tasks'
    task = sa.Column(sa.String(length=1024))
    task_id = sa.Column(sa.String(length=1024))
    created_ts = sa.Column(sa.BigInteger)
    status = sa.Column(sa.String(length=256))
    input = sa.Column(sajson.JSONField())
    result = sa.Column(sajson.JSONField())
    traceback = sa.Column(sa.Text)


class CeleryTaskModel(jslcrud.Model):
    schema = CeleryTaskSchema


class CeleryTaskCollection(jslcrud.Collection):
    schema = CeleryTaskSchema

    def search(self, *args, **kwargs):
        objs = super(CeleryTaskCollection, self).search(*args, **kwargs)
        if self.request.GET.get('refresh', '').lower() == 'true':
            for o in objs:
                meta = AsyncResult(o.data['task_id'])._get_task_meta()
                if meta['status'] == 'SUCCESS':
                    o.data['status'] = 'SUCCESS'
                    o.data['traceback'] = None
                    o.data['result'] = meta['result']
                elif meta['status'] == 'FAILURE':
                    o.data['status'] = 'FAILURE'
                    o.data['traceback'] = meta['traceback']
                    o.data['result'] = None
        return objs


class CeleryTaskMemoryStorage(MemoryStorage):
    model = CeleryTaskModel


class CeleryTaskSQLStorage(SQLStorage):
    model = CeleryTaskModel
    orm_model = CeleryTask


@BaseApp.celery_metastore(metastore='memorystorage', schema=CeleryTaskSchema)
def memory_metastore(metastore, schema):
    return CeleryTaskMemoryStorage


@BaseApp.celery_metastore(metastore='sqlstorage', schema=CeleryTaskSchema)
def sql_metastore(metastore, schema):
    return CeleryTaskSQLStorage


@BaseApp.path(model=CeleryTaskCollection, path='api/v1/task')
def get_task_collection(app, request):
    storage = app.get_celery_metastore(request)
    return CeleryTaskCollection(request, storage)


@BaseApp.json(model=CeleryTaskCollection, name='search')
def search_task(context, request):
    query = json.loads(request.GET.get('q', '{}'))
    if not query:
        query = None
    limit = int(request.GET.get('limit', 20))
    if limit > 100:
        limit = 100
    objs = context.search(query, limit=limit)
    return {'results': [obj.json() for obj in objs],
            'total': len(objs),
            'q': query}


@BaseApp.path(model=CeleryTaskModel, path='api/v1/task/{identifier}')
def get_task(app, request, identifier):
    storage = app.get_celery_metastore(request)
    return storage.get(identifier)


def cleanup(appClass, age_minutes=60):
    app = appClass()
    request = app.request_class(app=app, environ={'PATH_INFO': '/'})
    transaction.begin()
    now = int(time.time() * 1000)
    try:
        collection = get_task_collection(app, request)
        oldtasks = collection.search(
            query=rulez.field['created_ts'] < (
                now - (age_minutes * 60 * 1000))
        )
        for t in oldtasks:
            t.delete()
        transaction.commit()
    except:
        transaction.abort()
        raise


def refresh(appClass):
    app = appClass()
    request = app.request_class(app=app, environ={'PATH_INFO': '/'})
    transaction.begin()
    now = int(time.time() * 1000)
    try:
        collection = get_task_collection(app, request)
        objs = collection.search(
            query=rulez.and_(
                rulez.field['created_ts'] > (now - (60 * 60 * 1000)),
                rulez.field['status'] == 'SUBMITTED')
        )
        for o in objs:
            meta = AsyncResult(o.data['task_id'])._get_task_meta()
            if meta['status'] == 'SUCCESS':
                o.data['status'] = 'SUCCESS'
                o.data['traceback'] = None
                o.data['result'] = meta['result']
            elif meta['status'] == 'FAILURE':
                o.data['status'] = 'FAILURE'
                o.data['traceback'] = meta['traceback']
                o.data['result'] = None
        transaction.commit()
    except:
        transaction.abort()
        raise
