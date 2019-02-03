===================
Extended Attribute
===================

Resource models have the ability to be extended with extended
attributes. Extended attributes helps in the situation where
you are building a generic feature, but you
wish to allow downstream application to add additional data
fields into the generic resource model without having to
redefine the storage implementation with additional fields.

For example, a generic ``Event`` model would probably have ``title``,
``start_datetime`` and ``end_datetime`` on its model, and you have
created multiple views to display the Event, such as ``ical_view`` and
``xml_view``. Now, you are doing a project for CustomerA, which you need
to add additional data fields to ``Event`` model, eg: ``department_name``.
Normally you would have to modify ``EventSchema`` and its respective db schema
with additional fields, but with extended attributes, you can simply register a
extended attribute provider for ``Event`` model which would store the
value of ``department_name``.


.. autoclass:: morpfw.interfaces.IXattrProvider
   :members:
   :member-order: groupwise


Registering Extended Attribute Provider
========================================

MorpFW provides a default implementation for extended attribute provider
called ``FieldXattrProvider`` which stores extended attributes in ``xattr``
field of the resource.

To register an extended attribute provider for your model using
``FieldXattrProvider``, add the following code:

.. literalinclude:: _code/xattr.py
   :language: python
