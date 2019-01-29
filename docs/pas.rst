========================
Pluggable Auth Service
========================

MorpFW provides a built-in user, group & apikey management module and we called
it the Pluggable Auth Service (PAS). PAS by default uses SQLAlchemy backend,
but it is possible to override the storage engine used for it. Auth token
is handled through JWT.

PAS provides several key API endpoints such as registration, login, logout,
user management, group management, and api key management.

To enable PAS, you will need to mount the auth application on your application
by adding the following code in a new file. (eg: ``authn.py``)

.. literalinclude:: authapp.py
   :language: python

Afterwards, load the authentication policy on your application:

.. code-block:: yaml

   application:
      authn_policy: myproject.authn:AuthnPolicy

User Management & Authentication REST API
===========================================

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

.. http:post:: /auth/user/+register

   Register user

   .. todo:: examples

.. http:post:: /auth/user/{username}/+change_password

   Change password

   .. todo:: examples

.. note:: Individual user object management API is the same as Model REST API.

Group Management REST API
=========================

.. http:post:: /auth/group/{groupname}/+grant

   Grant role

   .. todo:: examples

.. http:post:: /auth/group/{groupname}/+revoke

   Revoke role

   .. todo:: examples

.. http:get:: /auth/group/{groupname}/+members

   List members and their roles

   .. todo:: examples