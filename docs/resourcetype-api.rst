=======================
Type System Python API
=======================

To manipulate resource types, we provide a simple mechanism
to interact with the collection and model. 

Lets take for example, the following resource type definition:

.. literalinclude:: exampleapp.py
   :language: python

Collection API
===============

Getting collection object
--------------------------

All resource types are registered in a central registry using ``typeinfo`` directive.
This allows you to query for collection by name, and use it in your program.

.. code-block:: python

   col = request.get_collection('test.page')

Creating records
-----------------

Records can be created through ``create`` method on collections.

.. code-block:: python

   page1 = col.create({'body': 'Hello world', 'value': 123})

``create`` method by default expect a dictionary with JSON serialized values, 
which mean, date and time would need to be passed to the method as 
Avro style date or time integers. (unix timestamp in miliseconds for 
``datetime``, number of days from epoch for ``date``)

If you already deserialized the values beforehand, and your date and time
are ``date`` or ``datetime`` objects. You will need to pass ``deserialize=False`` 
to the method.

.. code-block:: python

   page1 = col.create({'body': 'Hello world', 'value': 123}, deserialize=False)

By default, ``create`` method is set to insecure mode, which mean, it will allow
``state`` to be set during record creation (which ideally, you should not do this, 
because this should be handled by statemachine), and also will allow setting 
values for fields which are marked with ``initializable=False``. If you 
want to force security check, add ``secure=True`` to the parameter.

Getting individual record
--------------------------

If you know the UUID of a specific record, you can get the record using:

.. code-block:: python

   page1 = col.get(record_uuid) # record_uuid is a 32 char uuid string

Searching for records
---------------------

To search for records, you can use the ``search`` method. Filtering of search
results is using ``rulez`` JSON boolean statements, which you can refer
to `rulez documentation <https://rulez.readthedocs.io/en/latest/quickstart.html>`_
for details.

.. code-block:: python

   import rulez
   pages = col.search(rulez.field('value') == 123) # returns a list of Page model

Aggregation query
------------------

It is also possible to aggregate through the collection API. Aggregation
is done through a ``group`` query which uses the following structure:

.. code-block:: json

   {
      "<output_field>" : {
         "function": "<aggregation_function>",
         "field": "<field_name>"
      },
      "<output_field2>" : {
         "function": "<aggregation_function2>",
         "field": "<field_name2>"
      },
   }

For example:

.. code-block:: python

   group = {
      'hour': {
         'function': 'hourly',
         'field': 'created'
      },
      'count': {
         'function': 'count',
         'field': 'uuid'
      }
   }
   results = col.aggregate(group=group)

Only basic aggregation is supported through this API, primarily for the
purpose for presenting data for analytics. For more complex aggregation,
it is suggested that you develop that without using this aggregate API.

SQLStorage aggregate functions
...............................

Aggregate functions are storage specific, and currently, only following 
aggregate functions are supported for ``sqlstorage``:

 * Dimensions

   * ``year``
   * ``month``
   * ``day``
   * ``date``
   * ``hourly``

 * Metrics
 
   * ``count``
   * ``sum``
   * ``avg``
   * ``min``
   * ``max``

ElasticsearchStorage aggregate functions
.........................................

Aggregate functions are storage specific, and currently, only following 
aggregate functions are supported for ``elasticsearchstorage``:

 * Dimensions

   * ``year``
   * ``month``
   * ``day``
   * ``date``
   * ``interval_1m``
   * ``interval_15m``
   * ``interval_30m``
   * ``interval_1h``

 * Metrics

   * ``count``
   * ``sum``
   * ``avg``

Model API
=========

Reading data
----------------

Model is subscriptable and data can be accessed similar to a dictionary.

.. code-block:: python

   body = page1['body']

Updating data
--------------

Updating data on a record can be done using ``update`` method, which 
have similar API as Collection's ``create`` method. 

.. code-block:: python

   page1.update({'body': 'new body text'})

Deleting record
----------------

To delete a record, you can call the ``delete`` method.

.. code-block:: python

   page1.delete()


BLOB management
-----------------

As BLOBs are not stored in the main data storage, but rather in a separate
``blobstorage``, manipulating BLOBs are done usine a separate API.


Saving BLOB
............

To save a BLOB into a model, the API would be:

.. code-block:: python

   import os
   import mimetypes
   file_path = '/path/to/file'

   # in a view, you likely can get these information from
   # the request itself
   stat = os.stat(file_path)
   filename = os.path.basename(file_path)
   mt = mimetypes.guess_type(filename)

   with open('file','b') as f:
      page1.put_blob('attachment', f, 
                      filename=filename, 
                      mimetype=mt[0], size=stat.st_size)

   
If you are in a view, and file is uploaded as ``multipart/form-data``, you
can get ``mimetype`` and ``file`` object using following example:

.. code-block:: python

   # assuming file is uploaded as ``upload`` field

   @App.json(model=Page, name='upload-attachment', request_method='POST')
   def view(context, request):
       upload = request.POST.get('upload')

       filename = os.path.basename(upload.filename)
       mimetype = upload.type
       fileobj = upload.file

       context.put_blob('attachment', fileobj, filename=filename, mimetype=mimetype)
       return {"status": "ok"}

Reading BLOB
...............

Saved BLOBs can be read using:

.. code-block:: python

   blob = page1.get_blob('attachment')

   with blob.open() as f:
       data = f.read()

You can also return a BLOB as a streaming response in a view

.. code-block:: python

   @App.view(model=Page, name='get-attachment')
   def get_blob(context, request):
       blob = context.get_blob('attachment')
       return request.get_response(blob)

Deleting BLOBs
...............

To delete BLOBs, you can use:

.. code-block:: python

   page1.delete_blob('attachment')

Accessing state machine
-------------------------

If your model have a state machine registered with it, you can get
the state machine object using ``statemachine`` method.

.. code-block:: python

   # get state machine
   sm = page1.statemachine()
   # trigger ``approve`` transition
   sm.approve()

To learn more about state machine object, you can refer to `PyTransitions 
documentation <https://github.com/pytransitions/transitions>`_ as the 
state machine is built using it.


