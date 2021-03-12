import socket
import threading
from datetime import datetime

import click

from .cli import cli, load


def start_worker(ctx):
    print(threading.get_ident())
    param = load(ctx.obj["settings"])
    hostname = socket.gethostname()
    ws = param["settings"]["configuration"]["morpfw.celery"]
    now = datetime.utcnow().strftime(r"%Y%m%d%H%M")
    # scan
    param["factory"](param["settings"], instantiate=False)
    w = param["class"].celery.Worker(hostname="worker%s.%s" % (now, hostname), **ws)
    w.start()


@cli.command(help="alias to 'worker'")
@click.pass_context
def solo_worker(ctx):
    return start_worker(ctx)


@cli.command(help="start celery worker")
@click.pass_context
def worker(ctx):
    return start_worker(ctx)

