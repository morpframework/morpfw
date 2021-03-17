import cProfile
import os
import runpy
import sys
import time

import click
from alembic.config import main as alembic_main

from . import db, elasticstore, register_admin, scheduler, shell, start, worker
from .generate_config import genconfig


def run_module(argv=sys.argv):
    if len(argv) <= 1:
        print("Usage: %s [module]" % argv[0])
        sys.exit(1)
    mod = argv[1]
    sys.argv = argv[0:1] + argv[2:]
    runpy.run_module(mod, run_name="__main__", alter_sys=True)


def run_module_profile(argv=sys.argv):
    mod = argv[1]
    sys.argv = argv[0:1] + argv[2:]
    prof = cProfile.Profile()
    starttime = time.time()
    prof.enable()
    runpy.run_module(mod, run_name="__main__", alter_sys=True)
    prof.disable()
    endtime = time.time()
    print(f"Time taken: {endtime - starttime:.3f} seconds")
    outfile = mod + ".pstats"
    if os.path.exists(outfile):
        os.unlink(outfile)
    prof.dump_stats(outfile)
    print(f"Profiler result stored as {outfile}")


if __name__ == "__main__":
    main()
