import typing
import uuid
from datetime import datetime
from decimal import Decimal

import jsl
import sqlalchemy as sa
import sqlalchemy.orm as saorm
import sqlalchemy_jsonfield as sajson
from inverter import dc2pgsqla
from rulez import compile_condition
from sqlalchemy import Column, Index, MetaData, Table, func
from sqlalchemy import types as satypes
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import StatementError
from sqlalchemy.types import CHAR, TypeDecorator

from ..app import App
from .base import BaseStorage
from .sqlstorage import Base, MappedTable, SQLStorage

db_meta = Base.metadata

_mapped_models = {}


def construct_orm_model(schema, metadata, *, name=None):
    existing = _mapped_models.get(schema, None)
    if existing:
        return existing

    table = dc2pgsqla.convert(schema, metadata, name=name)

    class Table(MappedTable):

        __table__ = table

    saorm.mapper(Table, table)

    _mapped_models[schema] = Table
    return Table


class PgSQLStorage(SQLStorage):
    """
    At the moment this storage only works correctly with EntityContent.

    To use with code level SQLStorage, use `construct_orm_model`
    """

    _temp: dict = {}
    __table_name__ = None

    def __init__(self, request, metadata=None, blobstorage=None):
        super().__init__(request, blobstorage=blobstorage)
        self.metadata = metadata or db_meta
        self.metadata.bind = self.session.get_bind()

    @property
    def orm_model(self):
        name = getattr(self, "__table_name__", None)
        return construct_orm_model(self.model.schema, self.metadata, name=name)
