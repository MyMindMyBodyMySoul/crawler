=====
Usage
=====

If all dependencies are installed you can start the appropriate modules.

|

Quick Use
---------

For quick use just run:

::

    $ python hotcat.py

This starts by default all necessary processes in the correct order. To change the behavior edit :mod:`settings`.

|
|

Manually
--------

or start each required module manually or use an process control system like `supervisor <http://supervisord.org/>`_.

.. note::

    At least the :class:`~server.queue_manager.QueueManager` must be started.
    Also make sure that the project root path is available in PYTHONPATH.

- start the manager

::

    $ python server/queue_manager.py

- start the web server to handle incoming user requests

::

    $ python server/web.py


- start input worker to fill the queue with alexa top 1 million

::

    $ python worker/input_worker.py


- start sslyze worker to analyse the TLS configuration of the servers

::

    $ python worker/sslyze_worker.py


- start result worker to save sslyze results in to the mongodb.

::

    $ python worker/result_worker.py


- start status helper to get current status of the scan process

::

    $ python helper/status.py



