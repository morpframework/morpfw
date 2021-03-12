import click
import morpfw

from .cli import cli, load


@cli.command(help="start web server")
@click.option("-h", "--host", default=None, help="Host")
@click.option("-p", "--port", default=None, type=int, help="Port")
@click.option("--prod", default=False, type=bool, is_flag=True, help="Production mode")
@click.option(
    "--workers", default=None, type=int, help="Number of workers to run in  prod mode"
)
@click.pass_context
def start(ctx, host, port, prod, workers):

    param = load(ctx.obj["settings"], host, port)
    if prod:
        morpfw.runprod(
            param["factory"](param["settings"]),
            settings=param["settings"],
            host=param["host"],
            port=param["port"],
            ignore_cli=True,
            workers=workers,
        )
    else:
        morpfw.run(
            param["factory"](param["settings"]),
            settings=param["settings"],
            host=param["host"],
            port=param["port"],
            ignore_cli=True,
        )
