import os

from morpfw.crud import pubsub

from ...app import SQLApp
from ...crud.storage.sqlstorage import SQLStorage
from ...sql import Base, construct_orm_model
from ..common import get_client, make_request
from .workflow_common import App as BaseApp
from .workflow_common import (DeliveryOrderCollection, DeliveryOrderModel,
                              DeliveryOrderSchema, KitchenOrderCollection,
                              KitchenOrderModel, KitchenOrderSchema,
                              OrderCollection, OrderModel, OrderSchema,
                              ProcessWorkflowCollection, ProcessWorkflowModel,
                              ProcessWorkflowSchema, run_test)


class App(BaseApp, SQLApp):
    pass


class OrderStorage(SQLStorage):
    model = OrderModel
    orm_model = construct_orm_model(
        schema=OrderModel.schema, metadata=Base.metadata, name="test_order"
    )


@App.storage(model=OrderModel)
def get_order_storage(model, request, blobstorage):
    return OrderStorage(request, blobstorage)


class KitchenOrderStorage(SQLStorage):
    model = KitchenOrderModel
    orm_model = construct_orm_model(
        schema=KitchenOrderModel.schema,
        metadata=Base.metadata,
        name="test_kitchen_order",
    )


@App.storage(model=KitchenOrderModel)
def get_kitchen_order_storage(model, request, blobstorage):
    return KitchenOrderStorage(request, blobstorage)


class DeliveryOrderStorage(SQLStorage):
    model = DeliveryOrderModel
    orm_model = construct_orm_model(
        schema=DeliveryOrderModel.schema,
        metadata=Base.metadata,
        name="test_delivery_order",
    )


@App.storage(model=DeliveryOrderModel)
def get_delivery_order_storage(model, request, blobstorage):
    return DeliveryOrderStorage(request, blobstorage)


class ProcessWorkflowStorage(SQLStorage):
    model = ProcessWorkflowModel
    orm_model = construct_orm_model(
        schema=ProcessWorkflowModel.schema,
        metadata=Base.metadata,
        name="test_process_workflow",
    )


@App.storage(model=ProcessWorkflowModel)
def get_process_wf_storage(model, request, blobstorage):
    return ProcessWorkflowStorage(request, blobstorage)


def test_workflow(pgsql_db):
    config = os.path.join(
        os.path.dirname(__file__), "test_workflow_sqlstorage-settings.yml"
    )
    c = get_client(config)
    request = make_request(c.app)
    Base.metadata.create_all(bind=request.db_session.bind)
    run_test(c)
