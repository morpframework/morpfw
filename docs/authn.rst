===============
Authentication
===============

By default, morpfw uses ``user.id`` request url parameter as the username. This
is emulating similar what internal Hadoop services interact between nodes.

To change to a different authentication module, set ``application.authn_policy``
option in settings to either one of the following:

* ``morpfw.authn.pas:AuthnPolicy`` - Pluggable auth service which
  Gets user from either JWToken or ``X-API-KEY`` mapped user.
  Requires user and group management module
  to be mounted as the API key and token management comes from that module.
* ``morpfw.authn.useridparam:AuthnPolicy`` - Default. Gets username
  from ``user.id`` parameter in ``GET``. Validates remote address
  against ``security.allowed_nets`` to only trust provded hosts
* ``morpfw.authn.remoteuser:AuthnPolicy`` - Gets username
  from ``REMOTE_USER`` environment variable. Validates remote address
  against ``security.allowed_nets`` to only trust provded hosts


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
-------------------------------------------

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
-------------------------

.. http:post:: /auth/group/{groupname}/+grant

   Grant role

   .. todo:: examples

.. http:post:: /auth/group/{groupname}/+revoke

   Revoke role

   .. todo:: examples

.. http:get:: /auth/group/{groupname}/+members

   List members and their roles

   .. todo:: examples