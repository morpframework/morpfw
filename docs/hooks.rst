====================
Resource CRUD Hooks
====================

MorpFW includes several event hooks for CRUD activities so that you can slot
in your custom code without having to override the built-in views. Simply
implement the methods on your respective ``Collection`` and ``Model`` classes.

.. automethod:: morpfw.interfaces.ICollection.before_create

.. automethod:: morpfw.interfaces.IModel.after_created

.. automethod:: morpfw.interfaces.IModel.before_update

.. automethod:: morpfw.interfaces.IModel.after_updated

.. automethod:: morpfw.interfaces.IModel.before_delete

.. automethod:: morpfw.interfaces.IModel.before_blobput

.. automethod:: morpfw.interfaces.IModel.after_blobput

.. automethod:: morpfw.interfaces.IModel.before_blobdelete

