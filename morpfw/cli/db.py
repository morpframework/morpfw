import click
import morpfw

from ..alembic import drop_all
from .cli import cli, confirmation_dialog, load


@cli.command(help="Reset database")
@click.pass_context
def resetdb(ctx):
    param = load(ctx.obj["settings"])

    settings = param["settings"]

    if not confirmation_dialog():
        return

    with morpfw.request_factory(settings) as request:
        drop_all(request)


@cli.command(help="Vacuum database")
@click.pass_context
def vacuum(ctx):
    param = load(ctx.obj["settings"])

    settings = param["settings"]

    with morpfw.request_factory(settings) as request:

        types = request.app.config.type_registry.get_typeinfos(request)
        for typeinfo in types.values():

            collection = request.get_collection(typeinfo["name"])
            vacuum_f = getattr(collection.storage, "vacuum", None)
            if vacuum_f:
                print("Vacuuming %s" % typeinfo["name"])
                items = vacuum_f()
                print("%s record(s) affected" % items)


@cli.command(help="manage alembic migration")
@click.pass_context
def migration(ctx, options):
    pass

