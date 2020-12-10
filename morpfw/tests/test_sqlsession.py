import os

import morepath
import morpfw
import morpfw.sql
import yaml
from sqlalchemy.sql import func, select

from .test_sqlapp import get_pagecollection


def test_sqlsession(pgsql_db):
    morepath.scan(morpfw)
    with open(os.path.join(os.path.dirname(__file__), "test_sqlapp-settings.yml")) as f:
        settings = yaml.load(f.read(), Loader=yaml.Loader)

    with morpfw.request_factory(settings, scan=False) as request:
        morpfw.sql.Base.metadata.create_all(bind=request.db_session.bind)

    with morpfw.request_factory(settings, scan=False) as request:
        col = get_pagecollection(request)
        col.create({"title": "Hello world", "body": "Hello world"})

    with morpfw.request_factory(settings, scan=False) as request:
        col = get_pagecollection(request)
        items = col.search()
        assert len(items) == 1
        items[0].delete()

    with morpfw.request_factory(settings, scan=False) as request:
        col = get_pagecollection(request)
        items = col.search()
        assert len(items) == 0

    # test vacuuming
    with morpfw.request_factory(settings, scan=False) as request:
        col = get_pagecollection(request)
        orm_model = col.storage.orm_model
        session = col.storage.session
        tbl = orm_model.__table__
        sel_stmt = select([func.count(tbl.c.uuid)]).where(orm_model.deleted.isnot(None))
        res = session.execute(sel_stmt)
        assert res.fetchone()[0] == 1

        col.storage.vacuum()

        res = session.execute(sel_stmt)
        assert res.fetchone()[0] == 0

    # ensure clean
    with morpfw.request_factory(settings, scan=False) as request:
        col = get_pagecollection(request)
        orm_model = col.storage.orm_model
        session = col.storage.session
        tbl = orm_model.__table__
        sel_stmt = select([func.count(tbl.c.uuid)]).where(orm_model.deleted.isnot(None))
        res = session.execute(sel_stmt)
        assert res.fetchone()[0] == 0
