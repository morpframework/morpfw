import sys

from alembic.config import main as alembic_main

from . import db, elasticstore, register_admin, scheduler, shell, start, worker
from .cli import cli
from .generate_config import genconfig


def main():
    if "migration" in sys.argv:
        argv = sys.argv[sys.argv.index("migration") + 1 :]
        sys.exit(alembic_main(argv, "morpfw migration"))
    if "genconfig" in sys.argv:
        argv = sys.argv[sys.argv.index("genconfig") + 1 :]
        sys.exit(genconfig(argv))
    else:
        cli()


if __name__ == "__main__":
    main()
