===============
Authentication
===============

By default, morpfw uses ``user.id`` request url parameter as the username. This
is emulating similar what internal Hadoop services interact between nodes.

Available authentication modules are:

* ``morpfw.authn.pas:AuthnPolicy`` - Pluggable Auth Service which
  authenticate either using JWToken or ``X-API-KEY`` header.
  Requires Pluggable Auth Service app to be mounted.
  to be mounted as the API key and token management comes from that module.
* ``morpfw.authn.useridparam:AuthnPolicy`` - Default. Gets username
  from ``user.id`` parameter in ``GET``. Validates remote address
  against ``security.allowed_nets`` to only trust provded hosts
* ``morpfw.authn.remoteuser:AuthnPolicy`` - Gets username
  from ``REMOTE_USER`` environment variable. Validates remote address
  against ``security.allowed_nets`` to only trust provded hosts

To change to a different authentication module, update
``application.authn_policy`` in ``settings.yml``. Eg:

.. code-block:: yaml

   application:
      authn_policy: morpfw.authn.remoteuser:AuthnPolicy
