0.4.0 (2022-03-31)
------------------

- stable release


0.4.0b13 (2021-03-23)
---------------------

- generate path to migration script location when running genconfig
- fix config generator bug for dburi/dburl


0.4.0b12 (2021-03-23)
---------------------

- CLI now uses MFW_APP and MFW_HOME environment variable 
- if MFW_APP and MFW_HOME are set, settings file will be loaded
  from MFW_HOME
- generate-config avoids overwriting settings.yml if already exist

0.4.0b11 (2021-03-23)
---------------------

- fix issue with forgotten rename of ldap_uri to ldap_url


0.4.0b10 (2021-03-23)
---------------------

- semantic change dburi to dburl (BREAKS COMPAT)
- import oauth in root module so that hook_oauth_models is available


0.4.0b9 (2021-03-22)
--------------------

- alembic.ini is no longer required
- migration logging now uses dictConfig


0.4.0b8 (2021-03-19)
--------------------

- hidden fields marker support


0.4.0b7 (2021-03-19)
--------------------

- Added OAuth2 BackendAuthenticationWorkflow support
- Update to morepath 0.19
- Deprecate MORP_WORKDIR in favor of app specific homedir
- Added initial implementation for app level config generator. 
  New command `morpfw genconfig`
- Refactor cli components


0.4.0b6 (2021-01-31)
--------------------

- Added transition guarding capability


0.4.0b5 (2021-01-31)
--------------------

- Added permission configuration method in settings.yml
- Added ability to define readonly states
- Improvement in field protection implementation


0.4.0b4 (2021-01-27)
--------------------

- added workflow engine
- added metalink feature, where objects link can be recomputed
  from json data structure


0.4.0b3 (2020-12-28)
--------------------

- fix rtfd build issue


0.4.0b2 (2020-12-24)
--------------------

- reduce default size of creator/state fields to 256
- added vacumming capability to clean soft-deleted items
- added cascading deletion support
- remove dependencies on jsonobject, hydra
- added type referencing/backreferencing support
- allow including deleted items when querying
- added automated constructor of SQLA ORM model from dataclass
- save sha256sum of uploaded blobs
- added title provider for models and collection
- stop using autoscan in tests 
- added ESCapableRequests which provide ES client 
- fix count() implementation in ES storage
- added cli tools for elasticsearch index update
- added beaker.session and beaker.cache support
- fix ES aggregation issue and timezone issue
- added limit support in aggregate methods


0.4.0b1 (2020-11-20)
-------------------

  * ``dataclass`` based schema definition powered by ``inverter``

  * Simpler authn integration steps

  * ``colander`` based data validation

  * Simpler configuration structure with ``configuration`` option.

  * Async tasks does not create request by default, but rather provide
    parameter for instantiating request. Allowing finer control over commits
    and database connection locks.

  * Added memoization helpers and memoize regularly used model functions

  * Added timezone support in PAS 

  * Stability fixes
  
  * And many others ....



0.3.0 (2019-10-15)
------------------

Changes since 0.2.x:

 * Authentication is no longer a mounted app, this simplify programming as auth
   models are no longer treated special

 * Get rid of composite identifier as flat management of models is more
   maintainable and less confusing

 * Allow specifying prefix url for auth models, or devs can simply mount them
   wherever they link


