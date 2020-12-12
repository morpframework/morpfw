===========
Quickstart
===========

Bootstrapping a new project
============================

MorpFW requires Python 3.7 or newer to run. Python 3.6 is also supported but
you will need to install ``dataclasses`` backport into your environment.

The recommended way to install morpfw is to use `buildout <http://www.buildout.org>`_,
skeleton that is generated using ``mfw-template``. Please head to 
`mfw-template documentation <http://mfw-template.rtfd.org>`_ for tutorial.

Bootstrapping without ``mfw-template``
======================================

If you prefer to use ``virtualenv``, or other methods, you can follow these
steps.

First, lets get ``morpfw`` installed

.. code-block:: console

   $ pip install morpfw

If you are using buildout, version locks files are available at
``mfw_workspace`` repository: https://github.com/morpframework/mfw_workspace/tree/master/versions

Lets create an ``app.py``. In this example, we are creating a ``SQLApp`` application,
which meant to use ``SQLAlchemy`` as its primary data source, and provides ``SQLAlchemy``
transaction & session management.

.. literalinclude:: _code/app.py
   :language: python

``morpfw`` boot up application using a ``settings.yml`` file, so lets create one:

.. code-block:: yaml

   application:
      title: My First App
      class: app:App
   
Make sure you change your working directory to where ``app.py`` is, and you can 
then start the application using

.. code-block:: console

   $ PYTHONPATH=. morpfw -s settings.yml start

Creating a simple resource type / CRUD model
=============================================

``morpfw`` adds a type engine with RESTful CRUD on top of ``morepath``. To utilize
it, your models will need to follow a particular convention:

- A ``Collection`` is created that inherits ``morpfw.Collection`` 
- A ``Model`` is created that inherits ``morpfw.Model``
- Both ``Collection`` and ``Model`` class have a ``schema`` attribute that reference
  to a ``dataclass`` based schema
- Schema must be written using ``dataclass``, `following convention <https://inverter.rtfd.io>`_ 
  from ``inverter`` project. 
- A ``Storage`` class is implemented following the storage component API, and 
  registered against the ``Model`` class.
- A named typeinfo component is registered with details of the resource type. 

Following is an example boilerplate declaration of a resource type called ``page``, 
which will hook up the necessary RESTful API CRUD views for a simple data model
with ``title`` and ``body`` text.

.. literalinclude:: _code/page.py

Configuring Database Connection
--------------------------------

At the moment, ``morpfw.SQLStorage`` requires PostgreSQL to work correctly (due to
coupling to some PostgreSQL specific dialect feature). To configure the database
connection URI for SQLStorage, in ``settings.yml``, add in ``configuration`` option:

.. code-block:: yaml
   
   configuration:
      morpfw.storage.sqlstorage.dburi: 'postgresql://postgres:postgres@localhost:5432/app_db'


If you want to use `beaker <https://beaker.readthedocs.io/en/latest/>`_ for session and 
caching, you can also add:

.. code-block:: yaml

   configuration:
      ...
      morpfw.beaker.session.type: ext:database
      morpfw.beaker.session.url: 'postgresql://postgres:postgres@localhost:5432/app_cache'
      morpfw.beaker.cache.type: ext:database
      morpfw.beaker.cache.url: 'postgresql://postgres:postgres@localhost:5432/app_cache'
      ...


Initializing Database Tables
------------------------------

``morpfw`` provide integration with `Alembic <https://alembic.sqlalchemy.org/>`_ for 
generating SQLAlchemy based migrations. 

To initialize alembic directory, you can run:

.. code-block:: console

   $ morpfw migration init migrations

To hook up your application SQLAlchemy models for alembic scan, you will
need to edit ``env.py`` and add following imports, and configure ``target_metadata``
to include SQLStorage metadata:

.. code-block:: python

   from morpfw.crud.storage.sqlstorage import Base
   import app
   ...
   # configure target_metadata
   target_metadata = Base.metadata

As ``morpfw`` uses some additional sqlalchemy libraries, ``script.py.mako`` need
to also be edited to add additional imports:

.. code-block:: python

   import sqlalchemy_utils.types
   import sqlalchemy_jsonfield.jsonfield


Then, configure ``alembic.ini`` (generated together during ``migration init``) to
point to your database:

.. code-block:: ini

   [alembic]
   ...
   sqlalchemy.url: 'postgresql://postgres:postgres@localhost:5432/app_db'
   ...

Now you can use ``morpfw migration`` to generate a migration script based on defined
SQLAlchemy models.

.. code-block:: console

   $ PYTHONPATH=. morpfw migration revision --autogenerate -m "initialize"

You can then apply the migration using:

.. code-block:: console

   $ PYTHONPATH=. morpfw migration upgrade head

Finally you can start you application:

.. code-block:: console

   $ PYTHONPATH=. morpfw -s settings.yml start

CRUD REST API
=======================

If nothing goes wrong, you should get a CRUD REST API registered at 
``http://localhost:5000/pages/``.

.. code-block:: python

   >>> import requests
   >>> resp = requests.get('http://localhost:5000/pages')
   >>> resp.json()
   {...}

Lets create a page

.. code-block:: python

   >>> resp = requests.post('http://localhost:5000/pages/', json={
   ...     'body': 'hello world'
   ... })
   >>> objid = resp.json()['data']['uuid']
   >>> resp = requests.get('http://localhost:5000/pages/%s' % objid)
   >>> resp.json()
   {...}

Lets update the body text

   >>> resp = requests.patch(
   ...   'http://localhost:5000/pages/%s?user.id=foo' % objid, json={
   ...       'body': 'foo bar baz'
   ... })
   >>> resp = requests.get('http://localhost:5000/pages/%s' % objid)
   >>> resp.json()
   {...}

Lets do a search

   >>> resp = requests.get('http://localhost:5000/pages/+search')
   >>> resp.json()
   {...}

Lets delete the object

   >>> resp = requests.delete('http://localhost:5000/pages/%s' % objid)
   >>> resp.status_code
   200

Python CRUD API
=================

Python CRUD API is handled by ``Collection`` and ``Model`` objects. The
``typeinfo`` registry allows name based getter to ``Collection` from
the ``request`` object.

.. code-block:: python

   page_collection = request.get_collection('test.page')
   page = page_collection.get(page_uuid)

For more details, please refer to the :doc:`type system <resourcetype>` documentation.
