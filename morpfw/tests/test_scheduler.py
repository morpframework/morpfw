# FIXME: this test should run properly as unit test
from .common import get_client
from morpfw.app import SQLApp
import morpfw
import pytest
import morepath
from morpfw.authn.pas.storage.sqlstorage.dbmodel import User
import uuid


class App(SQLApp):
    pass


@App.periodic(name='test-cron', second=1)
def tick(request):
    q = request.db_session.query(User)
    for o in q.all():
        o.username = uuid.uuid4().hex
    request.db_session.add(o)
    print('tick!')


def main():
    morepath.autoscan()
    morepath.scan()
    App.commit()
    beat = App.celery.Beat()
    beat.run()
