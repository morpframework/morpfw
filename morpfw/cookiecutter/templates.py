from cookiecutter.main import cookiecutter
from ..cli import project
import click
from pkg_resources import resource_filename
import os
import yaml


@project.command()
def create_project():
    cookiecutter(resource_filename('morpfw.cookiecutter', 'project'))


@project.command()
@click.pass_context
def create_resource(ctx):
    project_name = ctx.obj['PROJECTRC']['project_name']
    cookiecutter(resource_filename('morpfw.cookiecutter', 'resource'),
                 output_dir=project_name)
