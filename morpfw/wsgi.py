from morpfw import create_app
import morpfw
import yaml
import os
from wsgigzip import gzip
import json
import importlib

APP = {'instance': None}


def wsgi_factory(app_factory):

    @gzip(mime_types=['application/json', 'text/json', 'text/plain', 'text/html'])
    def app(environ, start_response):
        if APP['instance']:
            return APP['instance'](environ, start_response)

        settings = json.loads(os.environ.get('MORP_SETTINGS'))

        application = app_factory(settings)
        APP['instance'] = application
        return application(environ, start_response)

    return app


def app(environ, start_response):
    app_mod, app_fname = os.environ['MORP_APP_FACTORY'].split(':')
    app_factory = getattr(importlib.import_module(app_mod), app_fname)
    return wsgi_factory(app_factory)(environ, start_response)
