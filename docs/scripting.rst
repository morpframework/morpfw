==============
Scripting API
==============

We also made it easy to use your developed application as command line script.
This is done through creating a ``request`` object in a script, and use
that request as how you would use in a view. This API is provided
so that you can easily build automation scripts using data stored
in your application, without having to maintain separate mechanism 
to connect to data and manipulate it.

When a request is instantiated, it will also establish the necessary
scaffolding and connection to databases, and when you close a request, 
data will be committed and connection would be closed. 

To instantiate a request object, you may use the following example

.. literalinclude:: _code/make_request.py
   :language: python


Settings provided to ``request_factory`` will inherit the default settings, 
so you are not required to provide all options.
