import tempfile
import typing
from dataclasses import dataclass, field
from datetime import date
from urllib.parse import quote

import rulez
from morpfw import Schema
from morpfw.app import BaseApp
from morpfw.crud import permission as crudperm
from morpfw.crud.model import Collection, Model
from morpfw.crud.statemachine.base import StateMachine
from morpfw.crud.workflow import WorkflowCollection, WorkflowModel


class App(BaseApp):
    pass


@App.permission_rule(model=Model, permission=crudperm.All)
def allow_all_model_access(identity, context, permission):
    return True


@App.permission_rule(model=Model, permission=crudperm.StateUpdate)
def allow_all_model_state_access(identity, context, permission):
    return True


@App.permission_rule(model=Collection, permission=crudperm.All)
def allow_all_collection_access(identity, context, permission):
    return True


def generate_workflow(request, data, model):
    if data["process_uuid"]:
        return data["process_uuid"]
    wfs = request.get_collection("tests.process_workflow")
    wf = wfs.create({})
    return wf.uuid


@dataclass
class OrderSchema(Schema):

    title: str = field(
        default="", metadata={"format": "text"},
    )
    process_uuid: typing.Optional[str] = field(
        default=None, metadata={"format": "uuid", "compute_value": generate_workflow}
    )


class OrderCollection(Collection):
    schema = OrderSchema


class OrderModel(Model):
    schema = OrderSchema


class OrderSM(StateMachine):

    states = ["new", "submitted", "closed", "cancelled"]
    transitions = [
        {"trigger": "submit", "source": "new", "dest": "submitted"},
        {"trigger": "complete", "source": "submitted", "dest": "closed"},
        {"trigger": "cancel", "source": ["new", "submitted"], "dest": "cancelled"},
    ]

    def trigger_workflow(self):
        context = self._context
        request = self._request
        wfs = request.get_collection("tests.process_workflow")
        wf = wfs.get(context["process_uuid"])
        wf.process(context)


@App.statemachine(model=OrderModel)
def order_statemachine(context):
    return OrderSM(context, after_state_change="trigger_workflow")


@App.path(model=OrderCollection, path="orders")
def order_collection_factory(request):
    storage = request.app.get_storage(OrderModel, request)
    return OrderCollection(request, storage)


@App.path(model=OrderModel, path="orders/{identifier}")
def order_model_factory(request, identifier):
    collection = order_collection_factory(request)
    return collection.get(identifier)


@App.typeinfo(name="tests.order", schema=OrderSchema)
def get_order_typeinfo(request):
    return {
        "title": "Order",
        "description": "Order type",
        "schema": OrderSchema,
        "collection": OrderCollection,
        "collection_factory": order_collection_factory,
        "model": OrderModel,
        "model_factory": order_model_factory,
    }


@dataclass
class KitchenOrderSchema(Schema):

    issue: typing.Optional[str] = field(
        default=None, metadata={"format": "text"},
    )
    process_uuid: typing.Optional[str] = field(
        default=None, metadata={"format": "uuid", "compute_value": generate_workflow}
    )


class KitchenOrderCollection(Collection):
    schema = KitchenOrderSchema


class KitchenOrderModel(Model):
    schema = KitchenOrderSchema


class KitchenOrderSM(StateMachine):

    states = ["new", "processing", "completed", "cancelled"]
    transitions = [
        {"trigger": "process", "source": "new", "dest": "processing"},
        {"trigger": "complete", "source": "processing", "dest": "completed"},
        {"trigger": "cancel", "source": ["new", "processing"], "dest": "cancelled"},
    ]

    def trigger_workflow(self):
        context = self._context
        request = self._request
        wfs = request.get_collection("tests.process_workflow")
        if context["process_uuid"] is None:
            wf = wfs.create({})
            context.update({"process_uuid": wf.uuid})
        else:
            wf = wfs.get(context["process_uuid"])
        wf.process(context)


@App.statemachine(model=KitchenOrderModel)
def kitchen_order_statemachine(context):
    return KitchenOrderSM(context, after_state_change="trigger_workflow")


@App.path(model=KitchenOrderCollection, path="kitchen_orders")
def kitchen_order_collection_factory(request):
    storage = request.app.get_storage(KitchenOrderModel, request)
    return KitchenOrderCollection(request, storage)


@App.path(model=KitchenOrderModel, path="kitchen_orders/{identifier}")
def kitchen_order_model_factory(request, identifier):
    collection = kitchen_order_collection_factory(request)
    return collection.get(identifier)


@App.typeinfo(name="tests.kitchen_order", schema=OrderSchema)
def get_kitchen_order_typeinfo(request):
    return {
        "title": "Kitchen Order",
        "description": "Kitchen Order type",
        "schema": KitchenOrderSchema,
        "collection": KitchenOrderCollection,
        "collection_factory": kitchen_order_collection_factory,
        "model": KitchenOrderModel,
        "model_factory": kitchen_order_model_factory,
    }


@dataclass
class DeliveryOrderSchema(Schema):

    receiver: typing.Optional[str] = field(
        default=None, metadata={"format": "text"},
    )
    process_uuid: typing.Optional[str] = field(
        default=None, metadata={"format": "uuid", "compute_value": generate_workflow}
    )


class DeliveryOrderCollection(Collection):
    schema = DeliveryOrderSchema


class DeliveryOrderModel(Model):
    schema = DeliveryOrderSchema


class DeliveryOrderSM(StateMachine):

    states = ["new", "shipped", "delivered", "cancelled"]
    transitions = [
        {"trigger": "ship", "source": "new", "dest": "shipped"},
        {"trigger": "complete", "source": "shipped", "dest": "delivered"},
        {"trigger": "cancel", "source": ["new", "shipped"], "dest": "cancelled"},
    ]

    def trigger_workflow(self):
        context = self._context
        request = self._request
        wfs = request.get_collection("tests.process_workflow")
        wf = wfs.get(context["process_uuid"])
        wf.process(context)


@App.statemachine(model=DeliveryOrderModel)
def delivery_order_statemachine(context):
    return DeliveryOrderSM(context, after_state_change="trigger_workflow")


@App.path(model=DeliveryOrderCollection, path="delivery_orders")
def delivery_order_collection_factory(request):
    storage = request.app.get_storage(DeliveryOrderModel, request)
    return DeliveryOrderCollection(request, storage)


@App.path(model=DeliveryOrderModel, path="delivery_orders/{identifier}")
def delivery_order_model_factory(request, identifier):
    collection = delivery_order_collection_factory(request)
    return collection.get(identifier)


@App.typeinfo(name="tests.delivery_order", schema=OrderSchema)
def get_delivery_order_typeinfo(request):
    return {
        "title": "Delivery Order",
        "description": "Delivery Order type",
        "schema": DeliveryOrderSchema,
        "collection": DeliveryOrderCollection,
        "collection_factory": delivery_order_collection_factory,
        "model": DeliveryOrderModel,
        "model_factory": delivery_order_model_factory,
    }


@dataclass
class ProcessWorkflowSchema(Schema):
    pass


class ProcessWorkflowCollection(WorkflowCollection):
    schema = ProcessWorkflowSchema


class ProcessWorkflowModel(WorkflowModel):
    schema = ProcessWorkflowSchema


@App.path(model=ProcessWorkflowCollection, path="process_workflows")
def process_workflow_collection_factory(request):
    storage = request.app.get_storage(ProcessWorkflowModel, request)
    return ProcessWorkflowCollection(request, storage)


@App.path(model=ProcessWorkflowModel, path="process_workflows/{identifier}")
def process_workflow_model_factory(request, identifier):
    collection = process_workflow_collection_factory(request)
    return collection.get(identifier)


@App.typeinfo(name="tests.process_workflow", schema=OrderSchema)
def get_process_workflow_typeinfo(request):
    return {
        "title": "Process Workflow",
        "description": "Process Workflow type",
        "schema": ProcessWorkflowSchema,
        "collection": ProcessWorkflowCollection,
        "collection_factory": process_workflow_collection_factory,
        "model": ProcessWorkflowModel,
        "model_factory": process_workflow_model_factory,
    }


@ProcessWorkflowModel.transition(model=OrderModel)
def process_order(wf, obj, request):
    kos = request.get_collection("tests.kitchen_order")
    if obj["state"] == "submitted":
        kos.create({"process_uuid": wf.uuid})


@ProcessWorkflowModel.transition(model=KitchenOrderModel)
def process_kitchenorder(wf, obj, request):
    dos = request.get_collection("tests.delivery_order")
    if obj["state"] == "completed":
        dos.create({"process_uuid": wf.uuid})


@ProcessWorkflowModel.transition(model=KitchenOrderModel)
def cancel_kitchenorder(wf, obj, request):
    if obj["state"] == "cancelled":
        # cancel all orders
        orders = request.get_collection("tests.order")
        os = orders.search(rulez.field("process_uuid") == wf.uuid)
        for o in os:
            sm = o.statemachine()
            sm.cancel()


@ProcessWorkflowModel.transition(model=DeliveryOrderModel)
def cancel_deliveryorder(wf, obj, request):
    if obj["state"] == "cancelled":
        # cancel all orders
        orders = request.get_collection("tests.order")
        os = orders.search(rulez.field("process_uuid") == wf.uuid)
        for o in os:
            sm = o.statemachine()
            sm.cancel()


@ProcessWorkflowModel.transition(model=DeliveryOrderModel)
def complete_deliveryorder(wf, obj, request):
    if obj["state"] == "delivered":
        # cancel all orders
        orders = request.get_collection("tests.kitchen_order")
        os = orders.search(rulez.field("process_uuid") == wf.uuid)
        for o in os:
            sm = o.statemachine()
            sm.complete()


def run_test(c):
    c.authorization = ("Basic", ("admin", "admin"))

    r = c.get("/orders")

    r = c.post_json("/orders", {"title": "Test Order"})

    order_uuid = r.json["data"]["uuid"]
    process_uuid = r.json["data"]["process_uuid"]

    r = c.get("/kitchen_orders/+search")
    assert len(r.json["results"]) == 0
    r = c.get("/delivery_orders/+search")
    assert len(r.json["results"]) == 0
    r = c.get("/process_workflows/+search")
    assert len(r.json["results"]) == 1

    r = c.post_json("/orders/%s/+statemachine" % order_uuid, {"transition": "submit"})

    r = c.get("/kitchen_orders/+search")
    assert len(r.json["results"]) == 1
    r = c.get("/process_workflows/+search")
    assert len(r.json["results"]) == 1
    r = c.get("/delivery_orders/+search")
    assert len(r.json["results"]) == 0

    r = c.get(
        "/kitchen_orders/+search?q=%s" % quote('process_uuid == "%s"' % process_uuid)
    )
    kitchenorder_uuid = r.json["results"][0]["data"]["uuid"]

    r = c.post_json(
        "/kitchen_orders/%s/+statemachine" % kitchenorder_uuid,
        {"transition": "process"},
    )

    r = c.get("/kitchen_orders/+search")
    assert len(r.json["results"]) == 1
    r = c.get("/process_workflows/+search")
    assert len(r.json["results"]) == 1
    r = c.get("/delivery_orders/+search")
    assert len(r.json["results"]) == 0

    r = c.post_json(
        "/kitchen_orders/%s/+statemachine" % kitchenorder_uuid,
        {"transition": "complete"},
    )

    r = c.get("/kitchen_orders/+search")
    assert len(r.json["results"]) == 1
    r = c.get("/process_workflows/+search")
    assert len(r.json["results"]) == 1
    r = c.get("/delivery_orders/+search")
    assert len(r.json["results"]) == 1

    r = c.get(
        "/delivery_orders/+search?q=%s" % quote('process_uuid == "%s"' % process_uuid)
    )
    deliveryorder_uuid = r.json["results"][0]["data"]["uuid"]

    r = c.post_json(
        "/delivery_orders/%s/+statemachine" % deliveryorder_uuid,
        {"transition": "cancel"},
    )

    r = c.get("/orders/%s" % order_uuid)
    assert r.json["data"]["state"] == "cancelled"

