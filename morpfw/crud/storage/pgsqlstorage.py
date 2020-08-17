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
from .sqlstorage import MappedTable, SQLStorage

db_meta = MetaData()

_mapped_models = {}


class PgSQLStorage(SQLStorage):

    _temp: dict = {}

    def __init__(self, request, metadata=None, blobstorage=None):
        super().__init__(request, blobstorage=blobstorage)
        self.metadata = metadata or db_meta
        self.metadata.bind = self.session.get_bind()

    @property
    def orm_model(self):
        existing = _mapped_models.get(self.model.schema, None)
        if existing:
            return existing

        table = dc2pgsqla.convert(self.model.schema, self.metadata)

        class Table(MappedTable):

            __table__ = table

        saorm.mapper(Table, table)

        _mapped_models[self.model.schema] = Table
        return Table
