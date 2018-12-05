import morpfw
import jsonobject
import sqlalchemy as sa

class App(morpfw.SQLApp):
   pass

class PageSchema(morpfw.Schema):
   body = jsonobject.StringProperty(required=False)

class PageCollection(morpfw.Collection):
   schema = PageSchema

class PageModel(morpfw.Model):
   schema = PageSchema

class Page(morpfw.SQLBase):
   __tablename__ = 'test_page'

   body = sa.Column(sa.String(length=1024))

class PageStorage(morpfw.SQLStorage):
   model = PageModel
   orm_model = Page

@App.path(model=PageCollection, path='pages')
def get_collection(request):
   storage = PageStorage(request)
   return PageCollection(request, storage)

@App.path(model=PageModel, path='pages/{identifier}')
def get_model(request, identifier):
   collection = get_collection(request)
   return collection.get(identifier)

if __name__ == '__main__':
    morpfw.run(App, {})
