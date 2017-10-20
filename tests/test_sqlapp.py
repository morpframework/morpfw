import morp
from morp import sql as morpsql
import sqlalchemy as sa
import jsl
from common import get_client


class App(morp.SQLApp):
    pass


class Page(morpsql.Base):
    __tablename__ = 'test_page'

    title = sa.Column(sa.String(length=1024))
    body = sa.Column(sa.Text)


class PageSchema(jsl.Document):
    class Options(object):
        title = 'page'
    title = jsl.StringField()
    body = jsl.StringField()


@App.jslcrud_identifierfields(schema=PageSchema)
def page_schema_identifier(schema):
    return ['uuid']


class PageCollection(morp.CRUDCollection):
    schema = PageSchema


class PageModel(morp.CRUDModel):
    schema = PageSchema


class PageStorage(morp.SQLStorage):
    model = PageModel
    orm_model = Page


@App.path(model=PageCollection, path='/')
def get_pagecollection(request):
    storage = PageStorage(request)
    return PageCollection(request, storage)


@App.path(model=PageModel, path='/{identifier}')
def get_page(request, identifier):
    storage = PageStorage(request)
    return storage.get(identifier)


App.authmanager_register(basepath='')

SETTINGS = {
    'authmanager': {
        'storage': 'sqlstorage',
        'default_user': 'defaultuser',
        'default_password': 'password'
    },
    'jwtauth': {
        'master_secret': 'secret',
        'leeway': 10
    },
    'sqlalchemy': {
        'dburi': 'sqlite:///%(here)s/app.db'
    }
}


if __name__ == '__main__':
    app = morp.create_app(App, SETTINGS)
    morp.run(app)


def test_morp_framework(pgsql_db):
    c = get_client(App)

    r = c.post_json(
        '/user/+login', {'username': 'defaultuser',
                         'password': 'password'})

    c.authorization = ('JWT', r.headers.get('Authorization').split()[1])

    r = c.get('/')
    assert r.json['schema']['title'] == 'page'
    assert len(r.json['schema']['properties']) == 2

    r = c.post_json(
        '/', {'title': 'Hello world', 'body': 'Lorem ipsum'})

    assert r.json['links'][0]['href'].startswith('http://localhost/')
    assert r.json['data']['title'] == 'Hello world'
    assert r.json['data']['body'] == 'Lorem ipsum'

    page_url = r.json['links'][0]['href']
    r = c.get(page_url)

    assert r.json['data']['title'] == 'Hello world'

    delete_link = r.json['links'][2]
    assert delete_link['method'] == 'DELETE'

    r = c.delete(delete_link['href'])

    r = c.get(page_url, expect_errors=True)

    assert r.status_code == 404
