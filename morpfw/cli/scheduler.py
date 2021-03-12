import socket

import click

from .cli import cli, load


@cli.command(help="start celery beat scheduler")
@click.pass_context
def scheduler(ctx):
    param = load(ctx.obj["settings"])
    hostname = socket.gethostname()
    ss = param["settings"]["configuration"]["morpfw.celery"]
    # scan
    param["factory"](param["settings"], instantiate=False)
    sched = param["class"].celery.Beat(hostname="scheduler.%s" % hostname, **ss)
    sched.run()

