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

   **Example request**:

   .. literalinclude:: _http/auth-register-post.http
      :language: http

   **Example response**:

   .. literalinclude:: _http/auth-register-post-response.http
      :language: http

.. http:post:: /auth/user/{username}/+change_password

   Change password

   **Example request**:

   .. literalinclude:: _http/auth-changepassword-post.http
      :language: http

   **Example response**:

   .. literalinclude:: _http/auth-changepassword-post-response.http
      :language: http

   .. todo:: examples

.. note:: individual user resource management api is the same as model rest api.

Group Management
=================

.. http:post:: /auth/group/{groupname}/+grant

   Grant role

   **Example request**:

   .. literalinclude:: auth-grant-post.http
      :language: http

   **Example response**:

   .. literalinclude:: auth-grant-post-response.http
      :language: http

.. http:post:: /auth/group/{groupname}/+revoke

   Revoke role

   **Example request**:

   .. literalinclude:: auth-revoke-post.http
      :language: http

   **Example response**:

   .. literalinclude:: auth-revoke-post-response.http
      :language: http


.. http:get:: /auth/group/{groupname}/+members

   List members and their roles

   **Example response**:

   .. literalinclude:: auth-members-get-response.http
      :language: http

.. note:: individual group resource management api is the same as model rest api.
