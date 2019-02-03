===============
Rules Provider
===============

Rules provider is a convenient plugin API which allows
you to register pluggable business rule class for your model following
the pattern we have for registering other pluggable providers.

If you wish to have a particular portion of your model processing logic
to be overrideable by downstream projects, you may use rules provider
to provide the processing logic.


Using Rules Provider
===========================

.. literalinclude:: _code/rulesprovider.py
   :language: python