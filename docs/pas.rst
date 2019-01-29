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
