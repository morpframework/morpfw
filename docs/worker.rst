===============================
Distributed Worker & Scheduler
===============================


MorpFW integrates with Celery to provide support for running asynchronous
& scheduled jobs. The ``morpfw`` command line tool provides subcomands which
makes it easy to start celery worker and scheduler for your project.

In asynchronous tasks triggered through web development API, MorpFW encodes the
WSGI request object and pass it to the worker so that you will get a very
similar behavior to web development when working with asynchronous tasks.

In scheduled task, a minimal request object is created and passed to the
scheduled task function.

Creating Async Task
=======================

Asynchronous task is implemented as signals which you can implement a
subscriber to the signal.

To create an async task subscribing to a signal, you can use the
``async_subscribe`` decorator on your ``App`` object. . The task can then be
triggered using ``request.async_dispatch``.

.. warning:: Because request object is passed to the worker, avoid using this
             in pages with uploads as it involves transfering the upload to the
             worker.

Following is a simple example implementation

.. literalinclude:: _code/async_subscribe.py
   :language: python


Creating Scheduled Job
=========================

Scheduled job can be implemented with a similar API style. MorpFW exposes
both the cron scheduler and periodic scheduler of Celery in an easy to use
API. 

Following is a simple example implementation

.. literalinclude:: _code/scheduler.py
   :language: python


Starting Celery Worker & Celery Beat Scheduler
==============================================

Worker and beat scheduler can be easily started up using:

.. code-block:: console

   $ # start worker
   $ morpfw -s settings.yml worker

   $ # start scheduler
   $ morpfw -s settings.yml scheduler
