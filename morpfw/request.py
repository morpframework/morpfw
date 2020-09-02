import importlib
import os
import threading
import typing
from importlib import import_module
from urllib.parse import urlparse

import pytz

import morepath
import morpfw
import sqlalchemy.orm
import transaction
from morepath.publish import resolve_model
from morepath.request import SAME_APP, LinkError
from morepath.request import Request as BaseRequest
from morepath.traject import parse_path
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from zope.sqlalchemy import ZopeTransactionEvents
from zope.sqlalchemy import register as register_session

from .exc import ConfigurationError

threadlocal = threading.local()


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
        scheme = e.get("X-FORWARDED-PROTO", None)
        host = e.get("X-FORWARDED-HOST", None)
        port = e.get("X-FORWARDED-PORT", None)
        if scheme and host and not port:
            return "{}://{}".format(scheme, host)
        if scheme and host and port:
            if (scheme == "https" and port == "443") or (
                scheme == "http" and port == "80"
            ):
                return "{}://{}".format(scheme, host)
            return "{}://{}:{}".format(scheme, host, port)
        return super().host_url

    def __enter__(self):
        self._cm_cwd = os.getcwd()
        transaction.begin()
        self.savepoint = transaction.savepoint()

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is not None:
            self.savepoint.rollback()
        transaction.commit()
        if os.path.exists(self._cm_cwd):
            os.chdir(self._cm_cwd)
        self.dispose_db_engines()

    def timezone(self):
        user_tz = getattr(self.identity, "timezone", None)
        if user_tz:
            return user_tz()
        return pytz.UTC

    def permits(self, model, permission):
        if isinstance(model, str):
            model = self.resolve_path(model)
        if isinstance(permission, str):
            perm_mod, perm_cls = permission.split(":")
            mod = import_module(perm_mod)
            klass = getattr(mod, perm_cls)
        else:
            klass = permission
        return self.app._permits(self.identity, model, klass)


class DBSessionRequest(Request):
    @property
    def _db_session(self):
        sessions = getattr(threadlocal, "mfw_db_sessions", None)
        if sessions is None:
            sessions = {}
            threadlocal.mfw_db_sessions = sessions

        return threadlocal.mfw_db_sessions

    @property
    def _db_engines(self):
        engines = getattr(threadlocal, "mfw_db_engines", None)
        if engines is None:
            engines = {}
            threadlocal.mfw_db_engines = engines

        return threadlocal.mfw_db_engines

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
            Session = sessionmaker(bind=engine)
            register_session(Session)
            self._db_session[name] = scoped_session(Session)
        return self._db_session[name]

    def clear_db_session(self, name=None):
        if name:
            if name in self._db_session.keys():
                self._db_session[name].expunge_all()
                self._db_session[name].close()
                del self._db_session[name]
        else:
            for k in list(self._db_session.keys()):
                self._db_session[k].expunge_all()
                self._db_session[k].close()
                self._db_session[k] = None
                del self._db_session[k]
        self.environ["morpfw.memoize"] = {}  # noqa

    def expunge_all(self, name=None):
        if name:
            if name in self._db_session.keys():
                self._db_session[name].expunge_all()
        else:
            for k in list(self._db_session.keys()):
                self._db_session[k].expunge_all()
        self.environ["morpfw.memoize"] = {}  # noqa

    def dispose_db_engines(self, name=None):
        if name:
            if name in self._db_engines.keys():
                if name in self._db_session.keys():
                    self._db_session[name].expunge_all()
                    self._db_session[name].close()
                    del self._db_session[name]
                self._db_engines[name].dispose()
                del self._db_engines[name]
        else:
            for k in list(self._db_engines.keys()):
                if k in self._db_session.keys():
                    self._db_session[k].expunge_all()
                    self._db_session[k].close()
                    del self._db_session[k]
                self._db_engines[k].dispose()
                del self._db_engines[k]
        self.environ["morpfw.memoize"] = {}  # noqa

    def get_collection(self, type_name):
        typeinfo = self.app.config.type_registry.get_typeinfo(
            name=type_name, request=self
        )
        col = typeinfo["collection_factory"](self)
        return col

    def resolve_path(self, path, app=SAME_APP):
        if app is None:
            raise LinkError("Cannot path: app is None")

        if app is SAME_APP:
            app = self.app

        request = self.__class__(self.environ.copy(), app, path_info=path)
        # try to resolve imports..

        return resolve_model(request)


COMMITTED_APPS = []


def request_factory(
    settings: dict,
    extra_environ: typing.Optional[dict] = None,
    scan: bool = True,
    app_factory_opts: typing.Optional[dict] = None,
):
    app_factory_opts = app_factory_opts or {}
    app_factory_opts["scan"] = scan
    extra_environ = extra_environ or {}

    if "application" not in settings:
        raise KeyError("'application' section is required in settings")
    if "factory" not in settings["application"]:
        raise KeyError("Missing application:factory entry in settings")
    if "class" not in settings["application"]:
        raise KeyError("Missing application:class entry in settings")

    factory_path = settings["application"]["factory"]
    mod, fname = factory_path.split(":")
    factory = getattr(importlib.import_module(mod), fname)

    app_path = settings["application"]["class"]
    mod, clsname = app_path.split(":")
    app_cls = getattr(importlib.import_module(mod), clsname)

    server_url = settings.get("server", {}).get("server_url", "http://localhost")
    parsed = urlparse(server_url)
    environ = {
        "PATH_INFO": "/",
        "wsgi.url_scheme": parsed.scheme,
        "SERVER_PROTOCOL": "HTTP/1.1",
        "HTTP_HOST": parsed.netloc,
        "REQUEST_METHOD": "GET",
    }
    environ.update(extra_environ)

    sys_environ = settings.get("environment", {}) or {}
    for k, v in sys_environ.items():
        if k not in os.environ.keys():
            os.environ[k] = v

    app = factory(settings, **app_factory_opts)
    app(environ, lambda *args: (lambda chunk: None))
    while not isinstance(app, morepath.App):
        wrapped = getattr(app, "app", None)
        if wrapped:
            app = wrapped
        else:
            raise ValueError("Unable to locate app object from middleware")

    return app.request_class(app=app, environ=environ)
