import morpfw
import morpfw.sql
import sqlalchemy as sa
import sqlalchemy_jsonfield as sajson
from .model import {{cookiecutter.type_name}}Model


class {{cookiecutter.type_name}}(morpfw.sql.Base):

    __tablename__ = 'resource_{{cookiecutter.module_name}}'

    title = sa.Column(sa.String(length=1024))
    description = sa.Column(sa.Text())


class {{cookiecutter.type_name}}Storage(morpfw.SQLStorage):
    model = {{cookiecutter.type_name}}Model
    orm_model = {{cookiecutter.type_name}}
