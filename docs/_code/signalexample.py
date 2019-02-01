from morpfw.crud import signals
from .app import App
from .model import PageModel


@App.subscribe(model=PageModel, signal=signals.OBJECT_CREATED)
def handle_create(request, context, signal):
    print("Object created")


@App.subscribe(model=PageModel, signal=signals.OBJECT_UPDATED)
def handle_update(request, context, signal):
    print("Object updated")


@App.subscribe(model=PageModel, signal=signals.OBJECT_TOBEDELETED)
def handle_deleted(request, context, signal):
    print("Deleting object")
    # raising exception here will prevent the deletion
