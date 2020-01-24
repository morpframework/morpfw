from pytest_postgresql import factories
import socket
from contextlib import closing
from pytest_rabbitmq.factories import rabbitmq_proc
import pytest
import pika
import os
import pytest
import shutil
import mirakuru
from elasticsearch import Elasticsearch
from pytest_postgresql import factories
import time

pgsql_proc = factories.postgresql_proc(
    executable='/usr/bin/pg_ctl', host='localhost', port=45678,
    user='postgres')
pgsql_db = factories.postgresql('pgsql_proc', db_name='morp_tests')

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


@pytest.fixture(scope='session')
def es_proc(request):
    port = 9085
    home_dir = '/tmp/elasticsearch_%s' % port
    os.environ['ES_HOME'] = home_dir
    command = [
        os.environ['ELASTICSEARCH_EXECUTABLE'],
        '-p', '/tmp/elasticsearch.%s.pid' % port,
        '-E', 'http.port=%s' % port,
        '-E', 'path.logs=/tmp/elasticsearch_%s_logs' % port,
        '-E', 'cluster.name=elasticsearch_cluster_%s' % port,
        '-E', "network.publish_host=127.0.0.1",
        '-E', 'index.store.type=mmapfs'
    ]
    es_proc = mirakuru.HTTPExecutor(
        command, shell=True, url='http://127.0.0.1:%s' % port)
    es_proc.start()

    def finalize_elasticsearch():
        es_proc.stop()
        if os.path.exists(home_dir):
            shutil.rmtree(home_dir)

    request.addfinalizer(finalize_elasticsearch)
    return es_proc


@pytest.fixture(scope='session')
def es_client(request):
    process = request.getfixturevalue('es_proc')
    if not process.running():
        process.start()

    hosts = "%s:%s" % (process.host, process.port)

    client = Elasticsearch(hosts=hosts)

    def drop_indexes():
        client.indices.delete(index='*')

    request.addfinalizer(drop_indexes)

    return client
