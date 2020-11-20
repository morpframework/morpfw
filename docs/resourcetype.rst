===============
Type System
===============

MorpFW CRUD & object management revolves around the idea of resource type. A
resource type represents a data model and its respective fields. Resource type
definition consist of a Schema, a Collection and a Model class. Collection is
very similar to the concept of database table, and model is very similar to a
row. Model have a Schema which defines the columns available in the Model.

When designing your application, it helps to think and model your application
around the concept of resource type model and collections because views are
attached to them.

Schema
=======

Resource type schema in MorpFW is defined through new python 3.7 `dataclass
library <https://docs.python.org/3/library/dataclasses.html>`_.


Schema in MorpFW is used for:

* data validation of JSON data on create/update REST API
* data validation on dictionary that is used to create a new instance of
  resource.
* generating JSON schema for publishing in REST API

When defining a schema, it is good that you inherit from ``morpfw.Schema``
as it defines the core metadata required for correct function of the framework.

.. code-block:: python

   import morpfw
   import typing
   from dataclasses import dataclass

   @dataclass
   class MySchema(morpfw.Schema):

       field1: typing.Optional[str] = None
       field2: typing.Optional[str] = 'hello world'

Due to the nature of `dataclass inheritance <https://docs.python.org/3/library/dataclasses.html#inheritance>`_,
your field definition must include default values, and if it does not have any,
you should define the field with ``typing.Optional`` data type with a default
value of ``None``

Model
======

Model is the object that is published on a MorpFW path. MorpFW base model class
provides the necessary API for model manipulation such as update, delete, save
and other model manipulation capabilities of MorpFW.

.. autoclass:: morpfw.interfaces.IModel
   :members:
   :member-order: groupwise

Collection
===========

Collection is the container for Model objects. Collection manages the single
type of Model and and provide collection level Model object management API
such as create, search and aggregate.

.. autoclass:: morpfw.interfaces.ICollection
   :members:
   :member-order: groupwise

Storage
========

Model and collection gets their data from a storage provider. It abstracts the
interface to storage backends, allowing custom storage backends to be
implemented.

.. autoclass:: morpfw.interfaces.IStorage
   :members:
   :member-order: groupwise
   :inherited-members:


BlobStorage
============

Storage provider may have a BLOB storage backend implemented which will handle
the management of BLOBs

.. autoclass:: morpfw.interfaces.IBlobStorage
   :members:

