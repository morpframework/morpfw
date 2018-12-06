===============
Authentication
===============

By default, morpfw uses ``user.id`` request url parameter as the username. This
is emulating similar what internal Hadoop services interact between nodes.

To change to a different authentication module, set ``application.authn_policy``
option in settings to either one of the following:

* ``morpfw.auth.policy.useridparam:AuthnPolicy`` - Default. Gets username
  from ``user.id`` parameter in ``GET``. Validates remote address
  against ``security.allowed_nets`` to only trust provded hosts
* ``morpfw.auth.policy.remoteuser:AuthnPolicy`` - Gets username
  from ``REMOTE_USER`` environment variable. Validates remote address
  against ``security.allowed_nets`` to only trust provded hosts
* ``morpfw.auth.policy.jwtapikey:AuthnPolicy`` - Gets user from either JWToken
  or ``X-API-KEY`` mapped user. Requires user and group management module
  to be mounted as the API key and token management comes from that module.



User and Group Management Module
=================================

You can also choose to make use of a built-in authentication manager which
provides API for register, login, logout, group membership and API key
management

.. literalinclude:: authapp.py
   :language: python


Accessing Auth API
-------------------

Refer ``test_auth.py`` in ``morpfw.tests`` for example on how to use the auth
API
