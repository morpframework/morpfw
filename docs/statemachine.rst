======================
State Machine
======================

Resources can be registered with a state machine to manage its states. MorpFW
uses PyTransitions as its default state machine engine and provides the 
REST API to transition the states of resources.

.. autoclass:: morpfw.interfaces.IStateMachine
   :members:
   :member-order: groupwise

Registering State Machine Provider
===================================

To register a state machine provider for your resource model, simply register
based on following example: 

.. literalinclude:: _code/statemachine.py
   :language: python