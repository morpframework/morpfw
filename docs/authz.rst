===============
Authorization
===============

Authorization in MorpFW make use of Morepath's ``permission_rule`` directive.

A practice in MorpFW is that we create assign permission rules on a separate,
permission rule only application which is then made as a superclass of the
current application. This manner allows us to create multiple authorization
policies which can be chosen from.

Built-in authorization policies are:

* ``morpfw.authz.pas:DefaultAuthzPolicy`` - Default policy which rejects access
  to all resources except for administrator user and user-specific APIs. This
  policy requires the Pluggable Auth Service to be enabled in the application.

To learn more about MorpFW authorization features, we suggest heading to
`Morepath's security documentation
<https://morepath.readthedocs.io/en/latest/security.html>`_.
