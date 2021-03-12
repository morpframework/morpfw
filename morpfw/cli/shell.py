import code
import cProfile
import os
import sys
import time

import click
import morpfw
import rulez
import transaction

from .cli import cli, load


@cli.command(help="Start MorpFW shell")
@click.option(
    "-e", "--script", required=False, help="Script to run before spawning shell"
)
@click.pass_context
def shell(ctx, script):
    return _start_shell(ctx, script)


@cli.command(help="Profile script")
@click.option("-e", "--script", required=False, help="Script to profile")
@click.pass_context
def profile(ctx, script):
    prof = cProfile.Profile()
    starttime = time.time()
    prof.enable()
    _start_shell(ctx, script, spawn_shell=False)
    prof.disable()
    endtime = time.time()
    print(f"Time taken: {endtime - starttime:.3f} seconds")
    outfile = script + ".pstats"
    if os.path.exists(outfile):
        os.unlink(outfile)
    prof.dump_stats(outfile)
    print(f"Profiler result stored as {outfile}")


@cli.command(help="Execute script")
@click.option("-e", "--script", required=False, help="Script to run")
@click.option(
    "--commit",
    default=False,
    required=False,
    type=bool,
    is_flag=True,
    help="Commit transaction",
)
@click.pass_context
def execute(ctx, script, commit):
    starttime = time.time()
    _start_shell(ctx, script, spawn_shell=False)
    if commit:
        transaction.commit()
    endtime = time.time()
    print(f"Time taken: {endtime - starttime:.3f} seconds")


def _start_shell(ctx, script, spawn_shell=True):
    from morepath.authentication import Identity

    param = load(ctx.obj["settings"])
    settings = param["settings"]
    request = morpfw.request_factory(settings)
    session = request.db_session

    def commit():
        transaction.commit()
        sys.exit()

    localvars = {
        "session": session,
        "request": request,
        "app": request.app,
        "settings": settings,
        "Identity": Identity,
        "commit": commit,
        "morpfw": morpfw,
        "rulez": rulez,
    }
    if script:
        with open(script) as f:
            src = f.read()
            glob = globals().copy()
            filepath = os.path.abspath(script)
            sys.path.insert(0, os.path.dirname(filepath))
            glob["__file__"] = filepath
            bytecode = compile(src, filepath, "exec")
            exec(bytecode, glob, localvars)
    if spawn_shell:
        _shell(localvars)


def _shell(vars):

    # readline is imported here because it screws up with click.prompt
    import readline
    import rlcompleter

    readline.set_completer(rlcompleter.Completer(vars).complete)
    readline.parse_and_bind("tab: complete")
    banner = "\nMorpFW Interactive Console\nAvailable globals : %s\n" % (
        ", ".join(vars.keys())
    )
    sh = code.InteractiveConsole(vars)
    sh.interact(banner=banner)

