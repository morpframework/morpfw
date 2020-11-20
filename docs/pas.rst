========================
Pluggable Auth Service
========================

MorpFW provides a built-in user, group & apikey management module and we called
it the Pluggable Auth Service (PAS). PAS by default uses SQLAlchemy backend,
but it is possible to override the storage engine used for it. Auth token
is handled through JWT.

PAS provides several key API endpoints such as registration, login, logout,
user management, group management, and api key management.

To enable PAS, your application have to be a subclass of ``morpfw.SQLApp``. 
``App.hook_auth_models()`` method should then be called to register PAS related
views. 

.. literalinclude:: authapp.py
   :language: python

Afterwards, load the PAS authentication policy in your application

.. code-block:: yaml

   configuration:
      morpfw.authn.policy: morpfw.authn.pas.policy:DefaultAuthnPolicy
