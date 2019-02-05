===========
Using Morp
===========

Bootstrapping a new project
============================

MorpFW requires Python 3.7 or newer to run. Python 3.6 is also supported but
you will need to install ``dataclasses`` backport into your environment.

The recommended way to install morpfw is to use
`pipenv <http://pipenv.rtfd.org>`_, or you can also use pip or virtualenv.

If you don't have pipenv installed yet, do:

.. code-block:: console

   $ sudo pip install pipenv>=2018.11.26

Lets create a new project. You can initialize new project using
``mfw-template`` tool:

.. code-block:: console

   $ sudo pip install mfw-template
   $ mfw-template create-project
   project_name [myproject]:
   project_url [http://myproject.com]:
   version [0.1.0]:
   author_name [John Doe]:
   author_email [johndoe@example.com]:
   short_description []:
   license [AGPLv3+]:


And start your project using:

.. code-block:: console

   $ cd myproject/ # replace with your project directory name
   $ pipenv install --python=python3.7 -e .
   $ pipenv run morpfw -s settings.yml start


Creating a simple resource type / CRUD model
=============================================

``mfw-template`` tool provide a quick way for you to generate a skeleton
resource type. Lets say you want to create a resource type called ``Page``

.. code-block:: console

   $ mfw-template create-resource
   type_name [Content]: Page
   module_name [page]:
   api_mount_path [/api/v1/page]: /pages


Lets start your application:

.. code-block:: console

   $ pipenv run morpfw -s settings.yml start


Accessing API
==============

Morp API endpoints requires authentication (we haven't figure out how to make
it optional yet), and the default authentication policy is to acquire current
username from ``user.id`` GET parameter.

.. code-block:: python

   >>> import requests
   >>> resp = requests.get('http://localhost:5000/pages?user.id=foo')
   >>> resp.json()
   {...}

Lets create a page

.. code-block:: python

   >>> resp = requests.post('http://localhost:5000/pages/?user.id=foo', json={
   ...     'body': 'hello world'
   ... })
   >>> objid = resp.json()['data']['uuid']
   >>> resp = requests.get('http://localhost:5000/pages/%s?user.id=foo' % objid)
   >>> resp.json()
   {...}

Lets update the body text

   >>> resp = requests.patch(
   ...   'http://localhost:5000/pages/%s?user.id=foo' % objid, json={
   ...       'body': 'foo bar baz'
   ... })
   >>> resp = requests.get('http://localhost:5000/pages/%s?user.id=foo' % objid)
   >>> resp.json()
   {...}

Lets do a search

   >>> resp = requests.get('http://localhost:5000/pages/+search')
   >>> resp.json()
   {...}

Lets delete the object

   >>> resp = requests.delete('http://localhost:5000/pages/%s?user.id=foo' % objid)
   >>> resp.status_code
   200
