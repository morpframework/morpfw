
import os

import sqlalchemy.orm
from morepath.request import Request as BaseRequest
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from zope.sqlalchemy import ZopeTransactionEvents
from zope.sqlalchemy import register as register_session

from .exc import ConfigurationError

Session = sessionmaker()
register_session(Session)


class Request(BaseRequest):
    def copy(self, *args, **kwargs):
        """
        Copy the request and environment object.

        This only does a shallow copy, except of wsgi.input
        """
        self.make_body_seekable()
        env = self.environ.copy()
        new_req = self.__class__(env, *args, **kwargs)
        new_req.copy_body()
        new_req.identity = self.identity
        return new_req

    def async_dispatch(self, signal, **kwargs):
        return self.app.async_dispatcher(signal).dispatch(self, **kwargs)

    @property
    def host_url(self):
        """
        The URL through the host (no path)
        """
        e = self.headers
        scheme = e.get('X-FORWARDED-PROTO', None)
        host = e.get('X-FORWARDED-HOST', None)
        port = e.get('X-FORWARDED-PORT', None)
        if scheme and host and not port:
            return '{}://{}'.format(scheme, host)
        if scheme and host and port:
            if ((scheme == 'https' and port == '443') or 
                    (scheme == 'http' and port == '80')):
                return '{}://{}'.format(scheme, host)
            return '{}://{}:{}'.format(scheme, host, port)
        return super().host_url




class DBSessionRequest(Request):

    _db_session: dict = {}
    _db_engines: dict = {}

    @property
    def db_session(self) -> sqlalchemy.orm.Session:
        return self.get_db_session("default")

    def get_db_engine(self, name="default"):
        # FIXME: Allow safe pooling, especially on the
        # worker side. Currently NullPool is used
        # to force worker to clean up connections
        # upon completion of tasks
        existing = self._db_engines.get(name, None)
        if existing:
            return existing

        settings = self.app._raw_settings
        config = settings["configuration"]

        cwd = os.environ.get("MORP_WORKDIR", os.getcwd())
        os.chdir(cwd)

        key = "morpfw.storage.sqlstorage.dburi"
        if "://" in name:
            dburi = name
        else:
            if name != "default":
                key = "morpfw.storage.sqlstorage.dburi.{}".format(name)

            if not config.get(key, None):
                raise ConfigurationError("{} not found".format(key))

            dburi = config[key]
        engine = sqlalchemy.create_engine(
            dburi, poolclass=NullPool, connect_args={"options": "-c timezone=utc"}
        )

        self._db_engines[name] = engine
        return engine

    def get_db_session(self, name="default"):

        if self._db_session.get(name, None) is None:
            engine = self.get_db_engine(name)
            self._db_session[name] = Session(bind=engine)
        return self._db_session[name]

    def clear_db_session(self, name=None):
        if name:
            if name in self._db_session.keys():
                self._db_session[name] = None
        else:
            for k in self._db_session.keys():
                self._db_session[k] = None
        self.environ["morpfw.memoize"] = {} # noqa

    def get_collection(self, type_name):
        typeinfo = self.app.config.type_registry.get_typeinfo(
            name=type_name, request=self
        )
        col = typeinfo["collection_factory"](self)
        return col
