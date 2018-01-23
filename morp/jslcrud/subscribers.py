from .app import App
from . import signals
from . import model
from datetime import datetime
from uuid import uuid4


@App.jslcrud_subscribe(signal=signals.OBJECT_CREATED, model=model.Model)
def set_uuid(app, request, obj, signal):
    uuid_field = app.get_jslcrud_uuidfield(obj.schema)
    if getattr(obj.schema, uuid_field, None):
        if obj.data.get(uuid_field, None) is None:
            obj.data[uuid_field] = uuid4().hex


@App.jslcrud_subscribe(signal=signals.OBJECT_CREATED, model=model.Model)
def set_created(app, request, obj, signal):
    if getattr(obj.schema, 'created', None):
        now = datetime.utcnow().isoformat()
        obj.data['created'] = now
        obj.data['last_modified'] = now


@App.jslcrud_subscribe(signal=signals.OBJECT_CREATED, model=model.Model)
def set_creator(app, request, obj, signal):
    if getattr(obj.schema, 'creator', None):
        obj.data['creator'] = request.remote_user or ''


@App.jslcrud_subscribe(signal=signals.OBJECT_UPDATED, model=model.Model)
def set_modified(app, request, obj, signal):
    if getattr(obj.schema, 'last_modified', None):
        obj.data['last_modified'] = datetime.utcnow().isoformat()
