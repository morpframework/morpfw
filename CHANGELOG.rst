0.3.0 (2019-10-15)
------------------

Changes since 0.2.x:

 * Authentication is no longer a mounted app, this simplify programming as auth
   models are no longer treated special

 * Get rid of composite identifier as flat management of models is more
   maintainable and less confusing

 * Allow specifying prefix url for auth models, or devs can simply mount them
   wherever they link


