===============
Authentication
===============

By default, morpfw uses no authentication. 

Available authentication modules are:

* ``morpfw.authn.noauth:AuthnPolicy`` - NOAUTH policy
* ``morpfw.authn.pas:AuthnPolicy`` - Pluggable Auth Service which
  authenticate either using JWToken or ``X-API-KEY`` header.
  Requires :doc:`Pluggable Auth Service <pas>` to be enabled as 
  the API key and token management comes from that module.
* ``morpfw.authn.useridparam:AuthnPolicy`` - Default. Gets username
  from ``user.id`` parameter in ``GET``. Validates remote address
  against ``morpfw.security.allowed_nets`` to only trust provded hosts
* ``morpfw.authn.remoteuser:AuthnPolicy`` - Gets username
  from ``REMOTE_USER`` environment variable. Validates remote address
  against ``morpfw.security.allowed_nets`` to only trust provded hosts

To change to a different authentication module, update
``morpfw.authn.policy`` configuration in ``settings.yml``. Eg:

.. code-block:: yaml

   configuration:
      morpfw.authn.policy: morpfw.authn.remoteuser:AuthnPolicy
      morpfw.authn.policy.settings: {}
