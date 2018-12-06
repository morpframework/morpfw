===============
Authentication
===============

By default, morpfw uses ``user.id`` request url parameter as the username. This
is emulating similar what internal Hadoop services interact between nodes.

You can also choose to make use of a built-in authentication manager which
provides API for register, login, logout, group membership and API key
management

.. literalinclude:: authapp.py
   :language: python


Accessing Auth API
====================

Refer ``test_auth.py`` in ``morpfw.tests`` for example on how to use the auth
API
