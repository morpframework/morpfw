=====================
Type System REST API
=====================

For each published resource type, several endpoints are automatically made
available by the framework to use. This is done through Morepath view 
inheritance on model/collection objects.

Lets take for example the following resource type definition:

.. literalinclude:: exampleapp.py
   :language: python


Collection
===========

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

   :query group: grouping structure
   :query q: ``rulez`` dsl based filter query
   :query order_by: string in ``field:order`` format where ``order`` is
                    ``asc`` or ``asc`` and ``field`` is the field name.

   **Example request**:

   .. literalinclude:: _http/pages-aggregate-get.py
      :language: python

   **Example response**:

   .. literalinclude:: _http/pages-aggregate-get-response.http
      :language: http

.. http:get:: /pages/+search

   The search API allows you to do advanced querying on your resources
   using Rulez query structure.

   :query select: jsonpath field selector
   :query q: ``rulez`` dsl based filter query 
   :query order_by: string in ``field:order`` format where ``order`` is
                    ``asc`` or ``asc`` and ``field`` is the field name.
   :query offset: result offset
   :query limit: result limit

   .. warning:: ``select`` query parameter would alter the response
                data structure from ``{"data":{},"links":[]}`` to 
                ``["val1","val2","val3" ... ]``

   **Example request**:

   .. literalinclude:: _http/pages-search-get.py
      :language: python

   **Example response**:

   .. literalinclude:: _http/pages-search-get-response.http
      :language: http


Model
=======

.. http:get:: /page/{uuid}

   Display resource data

   **Example response**:

   .. literalinclude:: _http/page-get-response.http
      :language: http


.. http:patch:: /page/{uuid}

   Update resource data

   **Example request**:

   .. literalinclude:: _http/page-patch.http
      :language: http

   **Example response**:

   .. literalinclude:: _http/page-patch-response.http
      :language: http


.. http:delete:: /page/{uuid}

   Delete resource

   **Example request**:

   .. literalinclude:: _http/page-delete.http
      :language: http

   **Example response**:

   .. literalinclude:: _http/page-delete-response.http
      :language: http


.. http:post:: /page/{uuid}/+blobs?field={blobfieldname}

   Upload blob using HTTP file upload

   **Example request**:

   .. literalinclude:: _http/page-blobs-post.py
      :language: python

   **Example response**:

   .. literalinclude:: _http/page-blobs-post-response.http
      :language: http


.. http:get:: /page/{uuid}/+blobs?field={blobfieldname}

   Download blob

.. http:delete:: /page/{uuid}/+blobs?field={blobfieldname}

   Delete blob

.. http:get:: /page/{uuid}/+xattr-schema

   Get JSON schema for validating extended attributes. This view is only
   available if your model have an extended attribute provider registered

.. http:get:: /page/{uuid}/+xattr

   Return extended attributes. This view is only
   available if your model have an extended attribute provider registered

   **Example response**:

   .. literalinclude:: _http/page-xattr-get-response.http
      :language: http

.. http:patch:: /page/{uuid}/+xattr

   Update extended attributes. This view is only
   available if your model have an extended attribute provider registered


   **Example request**:

   .. literalinclude:: _http/page-xattr-patch.http
      :language: http

   **Example response**:

   .. literalinclude:: _http/page-xattr-patch-response.http
      :language: http


.. http:post:: /pages/{uuid}/+statemachine

   Apply transition. This view is only available if your model have a
   state machine registered.

   **Example request**:

   .. literalinclude:: _http/page-statemachine-post.http
      :language: http

   **Example response**:

   .. literalinclude:: _http/page-statemachine-post-response.http
      :language: http
