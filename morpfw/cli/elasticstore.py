import click
import morpfw

from .cli import cli, confirmation_dialog, load


@cli.command(help="Update elasticsearch indexes")
@click.pass_context
def update_esindex(ctx):
    param = load(ctx.obj["settings"])

    settings = param["settings"]

    with morpfw.request_factory(settings) as request:

        types = request.app.config.type_registry.get_typeinfos(request)
        for typeinfo in types.values():
            collection = request.get_collection(typeinfo["name"])
            storage = collection.storage
            if isinstance(storage, morpfw.ElasticSearchStorage):
                print("Creating index %s .. " % storage.index_name, end="")
                if storage.create_index(collection):
                    print("OK")
                else:
                    if storage.update_index(collection):
                        print("UPDATED")
                    else:
                        raise AssertionError("Unknown error")


@cli.command(help="delete all elasticsearch indexes")
@click.pass_context
def reset_esindex(ctx):

    if not confirmation_dialog():
        return

    param = load(ctx.obj["settings"])

    settings = param["settings"]

    with morpfw.request_factory(settings) as request:

        types = request.app.config.type_registry.get_typeinfos(request)
        client = request.get_es_client()
        for typeinfo in types.values():
            collection = request.get_collection(typeinfo["name"])
            storage = collection.storage
            if isinstance(storage, morpfw.ElasticSearchStorage):
                print("Deleting index %s .. " % storage.index_name, end="")
                client.indices.delete(storage.index_name)
                print("OK")

