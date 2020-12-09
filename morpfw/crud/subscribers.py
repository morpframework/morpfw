from datetime import datetime
from uuid import uuid4

import pytz

from . import model, signals
from .app import App


@App.subscribe(signal=signals.OBJECT_CREATED, model=model.Model)
def set_uuid(app, request, obj, signal):
    uuid_field = app.get_uuidfield(obj.schema)
    if uuid_field in obj.schema.__dataclass_fields__.keys():
        if obj.data.get(uuid_field, None) is None:
            obj.data[uuid_field] = uuid4().hex


@App.subscribe(signal=signals.OBJECT_CREATED, model=model.Model)
def set_created(app, request, obj, signal):
    if "created" in obj.schema.__dataclass_fields__.keys():
        now = datetime.now(tz=pytz.UTC)
        obj.data["created"] = now
        obj.data["modified"] = now


@App.subscribe(signal=signals.OBJECT_CREATED, model=model.Model)
def set_creator(app, request, obj, signal):
    if "creator" in obj.schema.__dataclass_fields__.keys():
        obj.data["creator"] = request.identity.userid or None


@App.subscribe(signal=signals.OBJECT_UPDATED, model=model.Model)
def set_modified(app, request, obj, signal):
    if "modified" in obj.schema.__dataclass_fields__.keys():
        obj.data["modified"] = datetime.now(tz=pytz.UTC)
