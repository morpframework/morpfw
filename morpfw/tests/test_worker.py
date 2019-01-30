from .common import get_client, start_worker
from morpfw.app import SQLApp
from more.basicauth import BasicAuthIdentityPolicy
import time
import pytest


class App(SQLApp):
    pass


class Root(object):
    pass


def get_identity_policy():
    return BasicAuthIdentityPolicy


def verify_identity(identity):
    return True


@App.path(model=Root, path='')
def get_root(request):
    return Root()


@App.json(model=Root)
def index(context, request):
    subs = request.app.async_dispatcher(
        'test_signal').dispatch(request, obj={'data': 10})
    cel = request.app.celery
    res = []
    for s in subs:
        try:
            res.append(s.get())
        except:
            pass
    return res


@App.async_subscribe('test_signal')
def handler1(request, obj):
    obj['handler'] = 'handler1'
    obj['data'] += 1
    return obj


@App.async_subscribe('test_signal')
def handler2(request, obj):
    obj['handler'] = 'handler2'
    obj['data'] += 5
    return obj


@App.async_subscribe('test_signal')
def handler3(request, obj):
    obj['handler'] = 'handler3'
    raise Exception('Error')


# @pytest.fixture(scope='session')
# def celery_config():
#	return {
#		'broker_url': 'amqp://guest:guest@localhost:34567/',
#		'result_backend': 'db+postgresql://postgres@localhost:45678/morp_tests'
#	}


def test_signal(pgsql_db, pika_connection_channel, celery_worker):
    c = get_client(App, get_identity_policy=get_identity_policy,
                   verify_identity=verify_identity)

    c.authorization = ('Basic', ('dummy', 'dummy'))

    r = c.get('/')

    res = list(sorted(r.json, key=lambda x: x['handler']))
    assert res[0]['data'] == 11
    assert res[1]['data'] == 15
