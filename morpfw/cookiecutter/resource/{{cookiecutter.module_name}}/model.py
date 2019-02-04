import morpfw
from .schema import {{ cookiecutter.type_name }}Schema


class {{ cookiecutter.type_name }}Model(morpfw.Model):
    schema = {{ cookiecutter.type_name }}Schema


class {{ cookiecutter.type_name }}Collection(morpfw.Collection):
    schema = {{ cookiecutter.type_name }}Schema
