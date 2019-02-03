=================
Search Provider
=================

When building application with large dataset, it is common to not use your
primary storage to search for resources, but rather search through an
external indexing service such as ElasticSearch.

MorpFW provides a overrideable search provider API for you to intercept the
search mechanism and put your own search logic.

.. autoclass:: morpfw.interfaces.ISearchProvider
   :members:
   :member-order: groupwise



Overriding Search Provider
===========================

.. literalinclude:: _code/searchprovider.py
   :language: python

