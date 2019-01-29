=======
Views
=======

Morp inherits its view implementation from `morepath views
<https://morepath.readthedocs.io/en/latest/views.html>`_

Every ``morpfw.Model`` and ``morpfw.Collection`` are models which are published
on the defined path, and you can attach views to it.

Resource API
=============

For each published resource type, several endpoints are automatically made
available by the framework to use. This is done through Morepath view inheritance
on model/collection objects.

Lets take for example the following resource type definition:

.. literalinclude:: exampleapp.py
   :language: python


Collection REST API
--------------------

.. http:get:: /pages
   
   Display page collection metadata

   **Example Response**:

   .. literalinclude:: _http/pages-get-response.http
      :language: http

.. http:post:: /pages

   Create new page

   **Example request**:

   .. literalinclude:: _http/pages-post.http
      :language: http


   **Example response**:

   .. literalinclude:: _http/pages-post-response.http
      :language: http

.. http:get:: /pages/+aggregate

   The aggregate API allows you to query for aggregate
   of fields from your resource dataset.

   .. note:: This API is a bit ugly as it passes JSON object
             through GET parameter. We want to use a cleaner
             alternative, but have yet to get around it yet.

             Perhaps proper GraphQL implementation later

   **Example request**:

   .. literalinclude:: _http/pages-aggregate-get.py
      :language: python

   **Example response**:

   .. literalinclude:: _http/pages-aggregate-get-response.http
      :language: http

.. http:get:: /pages/+search

   The search API allows you to do advanced querying on your resources
   using Rulez query structure.

   .. note:: This API is a bit ugly as it passes JSON object
             through GET parameter. We want to use a cleaner
             alternative, but have yet to get around it yet.

             Perhaps proper GraphQL implementation later

   **Example request**:

   .. literalinclude:: _http/pages-search-get.py
      :language: python

   **Example response**:

   .. literalinclude:: _http/pages-search-get-response.http
      :language: http