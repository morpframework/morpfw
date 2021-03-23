import sys

import click
from alembic.config import CommandLine as AlembicCLI
from alembic.config import Config as AlembicCfg
from alembic.config import main as alembic_main

from . import db, elasticstore, register_admin, scheduler, shell, start, worker
from .cli import cli
from .generate_config import genconfig as genconfig_main


@cli.command(help="generate config file")
@click.pass_context
def generate_config(ctx, options):
    pass


def main():
    if "generate-config" in sys.argv:
        argv = sys.argv[sys.argv.index("generate-config") + 1 :]
        sys.exit(genconfig_main(argv))
    else:
        cli()


if __name__ == "__main__":
    main()

