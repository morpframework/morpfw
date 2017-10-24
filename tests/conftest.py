from pytest_postgresql import factories
import socket
from contextlib import closing
from pytest_rabbitmq.factories import rabbitmq_proc
import pytest
import pika

pgsql_proc = factories.postgresql_proc(
    executable='/usr/bin/pg_ctl', host='localhost', port=45678,
    user='postgres')
pgsql_db = factories.postgresql('pgsql_proc', db='morp_tests')

rabbitmq_pika_proc = rabbitmq_proc(
    server='/usr/lib/rabbitmq/bin/rabbitmq-server',
    port=34567)


@pytest.fixture
def pika_connection_channel(rabbitmq_pika_proc):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost', port=34567,
                                  credentials=pika.PlainCredentials('guest',
                                                                    'guest')))
    channel = connection.channel()
    return [connection, channel]
