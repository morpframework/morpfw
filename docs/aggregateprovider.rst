====================
Aggregate Provider
====================

When building application with large dataset, it is common to pre-aggregate
data on the data management layer and only query for aggregate from precomputed
aggregate storage.

MorpFW provides a overrideable aggregate provider API for you to intercept the
aggregate mechanism and put your own aggregate logic.

.. autoclass:: morpfw.interfaces.IAggregateProvider
   :members:
   :member-order: groupwise



Overriding Aggregate Provider
==============================

.. literalinclude:: _code/aggregateprovider.py
   :language: python


