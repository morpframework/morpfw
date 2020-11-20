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


