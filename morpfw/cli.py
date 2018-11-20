from argh import arg, dispatch_commands
import os
import sys
from .main import create_app
import morepath
import yaml
import morpfw


@arg('-a', '--app', required=True, help='Path to App class')
@arg('-s', '--settings', required=True, help='Path to settings.yml')
@arg('-h', '--host', default='127.0.0.1', help='Host')
@arg('-p', '--port', default=5432, type=int, help='Port')
def start(app=None, settings=None, host=None, port=None):
    sys.path.append(os.getcwd())
    mod, clsname = app.split(':')
    app_cls = getattr(__import__(mod), clsname)

    settings = yaml.load(open(settings))
    appobj = create_app(app_cls, settings)
    morpfw.run(appobj, host=host, port=port, ignore_cli=True)


def run():
    dispatch_commands([start])
