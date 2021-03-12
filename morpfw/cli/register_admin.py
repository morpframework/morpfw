import click
import morpfw

from .cli import cli, load


@cli.command(help="register administrator user (only for app using PAS)")
@click.option("-u", "--username", required=True, help="Username", prompt=True)
@click.option("-e", "--email", required=True, help="Email address", prompt=True)
@click.option(
    "-p",
    "--password",
    required=True,
    help="Password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
)
@click.pass_context
def register_admin(ctx, username, email, password):
    param = load(ctx.obj["settings"])
    settings = param["settings"]
    with morpfw.request_factory(
        settings, extra_environ={"morpfw.nomemoize": True}
    ) as request:
        user = morpfw.create_admin(
            request, username=username, password=password, email=email
        )
        if user is None:
            print("Application is not using Pluggable Auth Service")

