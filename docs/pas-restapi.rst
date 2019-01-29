==================
PAS REST API
==================

Authentication
================

.. http:post:: /auth/user/+login

   Log into the system

   **Example request**:

   .. literalinclude:: _http/auth-login-post.http
      :language: http

   **Example response**:

   .. literalinclude:: _http/auth-login-post-response.http
      :language: http


.. http:get:: /auth/user/+refresh_token

   Return new token

   **Example request**:

   .. literalinclude:: _http/auth-refreshtoken-get.http
      :language: http

   **Example response**:

   .. literalinclude:: _http/auth-refreshtoken-get-response.http
      :language: http


User Management 
================


.. http:post:: /auth/user/+register

   Register user

   .. todo:: examples

.. http:post:: /auth/user/{username}/+change_password

   Change password

   .. todo:: examples

.. note:: Individual user object management API is the same as Model REST API.

Group Management
=================

.. http:post:: /auth/group/{groupname}/+grant

   Grant role

   .. todo:: examples

.. http:post:: /auth/group/{groupname}/+revoke

   Revoke role

   .. todo:: examples

.. http:get:: /auth/group/{groupname}/+members

   List members and their roles

   .. todo:: examples