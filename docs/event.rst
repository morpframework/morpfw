=============
Event Signal
=============

Key events in resource management lifecycle would trigger signals which can
be subscribed to. Key signals triggered by the type system includes:

* ``morpfw.crud.signals.OBJECT_CREATED`` - triggered after resource creation
* ``morpfw.crud.signals.OBJECT_UPDATED`` - triggered after resource is updated
* ``morpfw.crud.signals.OBJECT_TOBEDELETED`` - triggered before deletion of
  resource

Registering Signal Subscriber
==============================

To hook up a function that subscribe to a signal, you can use the ``subscribe``
method on your ``App`` object:

.. literalinclude:: _code/signalexample.py
   :language: python


Publishing Custom Event Signal
===============================

Custom event signal can be triggered using ``signal_publish`` method of
``App``:

.. literalinclude:: _code/signalpublish.py
   :language: python



