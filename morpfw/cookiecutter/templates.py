from cookiecutter.main import cookiecutter
from ..cli import project
import click
from pkg_resources import resource_filename


@project.command()
def create_project():
    cookiecutter(resource_filename('morpfw.cookiecutter', 'project'))
