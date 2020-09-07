import uuid
from datetime import datetime
from decimal import Decimal

import pytz

import jsl
import sqlalchemy as sa
import sqlalchemy_jsonfield as sajson
from rulez import compile_condition
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import StatementError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import CHAR, TypeDecorator

from ..app import App
from .base import BaseStorage


class SQLStorage(BaseStorage):

    _temp: dict = {}

    @property
    def orm_model(self):
        raise NotImplementedError

    @property
    def session(self):
        return self.request.db_session

    def create(self, collection, data):
        o = self.orm_model()
        dst = self.app.get_dataprovider(self.model.schema, o, self)
        src = self.app.get_dataprovider(self.model.schema, data, self)
        for k, v in src.items():
            dst[k] = v
        m = self.model(self.request, collection, o)
        identifier = m.identifier
        self.session.add(o)
        self.session.flush()
        self.session.refresh(o)
        return m

    def aggregate(self, query=None, group=None, order_by=None):
        group_bys = []
        group_bys_map = {}

        if group:
            fields = []
            for k, v in group.items():
                if isinstance(v, str):
                    c = getattr(self.orm_model, v)
                    fields.append(c)
                    group_bys.append(c)
                elif isinstance(v, dict):
                    ff = v["function"]
                    f = v["field"]
                    c = getattr(self.orm_model, f)
                    if ff == "count":
                        op = func.count(c).label(k)
                        fields.append(op)
                        group_bys_map[k] = op
                    elif ff == "sum":
                        op = func.sum(c).label(k)
                        fields.append(op)
                        group_bys_map[k] = op
                    elif ff == "avg":
                        op = func.avg(c).label(k)
                        fields.append(op)
                        group_bys_map[k] = op
                    elif ff == "min":
                        op = func.min(c).label(k)
                        fields.append(op)
                        group_bys_map[k] = op
                    elif ff == "max":
                        op = func.max(c).label(k)
                        fields.append(op)
                        group_bys_map[k] = op
                    elif ff == "year":
                        op = func.date_part("YEAR", c).label(k)
                        fields.append(op)
                        group_bys.append(op)
                        group_bys_map[k] = op
                    elif ff == "month":
                        op = func.date_part("MONTH", c).label(k)
                        fields.append(op)
                        group_bys.append(op)
                        group_bys_map[k] = op
                    elif ff == "day":
                        op = func.date_part("DAY", c).label(k)
                        fields.append(op)
                        group_bys.append(op)
                        group_bys_map[k] = op
                    elif ff == "date":
                        op = func.to_char(c, "YYYY-MM-DD").label(k)
                        fields.append(op)
                        group_bys.append(op)
                        group_bys_map[k] = op
                    else:
                        raise ValueError("Unknown function %s" % ff)
        else:
            fields = [self.orm_model]

        if query:
            f = compile_condition("sqlalchemy", query)
            filterquery = f(self.orm_model)
            filterquery = sa.and_(self.orm_model.deleted.is_(None), filterquery)
            q = self.session.query(*fields).filter(filterquery)
        else:
            q = self.session.query(*fields).filter(self.orm_model.deleted.is_(None))

        if order_by is not None:
            col = order_by[0]
            d = order_by[1]
            if d not in ["asc", "desc"]:
                raise KeyError(d)
            if col in group_bys_map:
                colattr = group_bys_map[col]
            else:
                colattr = getattr(self.orm_model, col)
            if d == "desc":
                q = q.order_by(colattr.desc())
            else:
                q = q.order_by(colattr)

        if group_bys:
            q = q.group_by(*group_bys)

        results = []
        try:
            q_res = q.all()
        except StatementError:
            empty_res = {}
            for f in fields:
                empty_res[f.key] = 0
            return [empty_res]

        for o in q_res:
            d = o._asdict()
            for k, v in d.items():
                if isinstance(v, datetime):
                    d[k] = v.isoformat()
                elif isinstance(v, Decimal):
                    d[k] = float(v)
                elif isinstance(v, uuid.UUID):
                    d[k] = v.hex

            results.append(d)
        return results

    def search(self, collection, query=None, offset=None, limit=None, order_by=None):
        if query:
            f = compile_condition("sqlalchemy", query)
            filterquery = f(self.orm_model)
            q = self.session.query(self.orm_model).filter(
                sa.and_(self.orm_model.deleted.is_(None), filterquery)
            )
        else:
            q = self.session.query(self.orm_model).filter(
                self.orm_model.deleted.is_(None)
            )

        if order_by is not None:
            col = order_by[0]
            d = order_by[1]
            if d not in ["asc", "desc"]:
                raise KeyError(d)
            colattr = getattr(self.orm_model, col)
            if d == "desc":
                q = q.order_by(colattr.desc())
            else:
                q = q.order_by(colattr)
        if offset is not None:
            q = q.offset(offset)
        if limit is not None:
            q = q.limit(limit)

        yield_per = self.request.environ.get("morpfw.sqlstorage.yield_per", None)
        if yield_per is None:
            try:
                return [self.model(self.request, collection, o) for o in q.all()]
            except StatementError:
                return []
        else:
            try:
                return [
                    self.model(self.request, collection, o)
                    for o in q.yield_per(yield_per)
                ]
            except StatementError:
                return []

    def get(self, collection, identifier):
        qs = []
        idfield = self.app.get_identifierfield(self.model.schema)
        q = self.session.query(self.orm_model).filter(
            sa.and_(
                self.orm_model.deleted.is_(None),
                getattr(self.orm_model, idfield) == identifier,
            )
        )
        try:
            r = q.first()
        except StatementError:
            return None
        if not r:
            return None
        return self.model(self.request, collection, r)

    def get_by_id(self, collection, id):
        q = self.session.query(self.orm_model).filter(self.orm_model.id == id)
        r = q.first()
        if not r:
            return None
        return self.model(self.request, collection, r)

    def get_by_uuid(self, collection, uuid):
        uuid_field = self.app.get_uuidfield(self.model.schema)
        if getattr(self.orm_model, uuid_field, None) is None:
            raise AttributeError(
                "%s does not have %s field" % (self.orm_model, uuid_field)
            )
        qs = getattr(self.orm_model, uuid_field) == uuid
        q = self.session.query(self.orm_model).filter(qs)
        r = q.first()
        if not r:
            return None
        return self.model(self.request, collection, r)

    def update(self, collection, identifier, data):
        qs = []

        idfield = self.app.get_identifierfield(self.model.schema)
        qs.append(getattr(self.orm_model, idfield) == identifier)
        qs.append(self.orm_model.deleted.is_(None))
        q = self.session.query(self.orm_model).filter(sa.and_(*qs))

        r = q.first()
        if not r:
            raise ValueError(identifier)

        d = self.app.get_dataprovider(self.model.schema, r, self)
        for k, v in data.items():
            if d.get(k, None) != v:
                d[k] = v

        return self.model(self.request, collection, r)

    def delete(self, identifier, model, **kwargs):
        permanent = kwargs.get("permanent", False)
        if permanent:
            model.delete()
        else:
            model["deleted"] = datetime.now(tz=pytz.UTC)


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.

    """

    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return uuid.UUID(value)


class MappedTable(object):
    pass


class BaseMixin(MappedTable):

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    uuid = sa.Column(GUID, default=uuid.uuid4, index=True, unique=True)
    created = sa.Column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(tz=pytz.UTC),
        index=True,
    )
    creator = sa.Column(sa.String(length=1024))
    modified = sa.Column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(tz=pytz.UTC),
        index=True,
    )
    state = sa.Column(sa.String(length=1024), index=True)
    deleted = sa.Column(sa.DateTime(timezone=True), index=True)
    blobs = sa.Column(sajson.JSONField)
    xattrs = sa.Column(sajson.JSONField)


Base = declarative_base(cls=BaseMixin)
