from pytest_postgresql import factories
import socket
from contextlib import closing

pgsql_proc = factories.postgresql_proc(
    executable='/usr/bin/pg_ctl', host='localhost', port=45678,
    user='postgres')
pgsql_db = factories.postgresql('pgsql_proc', db='morp_tests')
