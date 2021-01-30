import os

from ...app import SQLApp
from ...crud.storage.sqlstorage import SQLStorage
from ...sql import Base, construct_orm_model
from ..common import create_admin, get_client, make_request
from .auth_crud import App as BaseApp
from .auth_crud import (
    Object1Model,
    Object1Schema,
    Object2Model,
    Object2Schema,
    run_test,
)


class App(BaseApp, SQLApp):
    pass


App.hook_auth_models()


class Object1Storage(SQLStorage):
    model = Object1Model
    orm_model = construct_orm_model(schema=Object1Schema, metadata=Base.metadata,)


@App.storage(model=Object1Model)
def get_object1_storage(model, request, blobstorage):
    return Object1Storage(request, blobstorage)


class Object2Storage(SQLStorage):
    model = Object2Model
    orm_model = construct_orm_model(schema=Object2Schema, metadata=Base.metadata,)


@App.storage(model=Object2Model)
def get_object2_storage(model, request, blobstorage):
    return Object2Storage(request, blobstorage)


def test_auth_crud(pgsql_db):
    config = os.path.join(
        os.path.dirname(__file__), "test_auth_crud_sqlstorage-settings.yml"
    )
    c = get_client(config)
    request = make_request(c.app)
    Base.metadata.create_all(bind=request.db_session.bind)
    create_admin(c.mfw_request, "admin", "password", "admin@localhost.localdomain")

    run_test(c)
