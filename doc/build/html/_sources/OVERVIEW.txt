========
Overview
========

Hotcat follows the consumer-producer pattern. There is a manager that manages all tasks and communication
between all other modules via tcp, the so called :class:`~server.queue_manager.QueueManager`. Therefore it is necessary
that the :class:`~server.queue_manager.QueueManager` runs. All other modules can then connect
to the :class:`~server.queue_manager.QueueManager` and pick up or deliver tasks.
Each module runs in a separate process, but it is not necessary that all modules run.
By default, all modules are started, but this can be changed in the :mod:`settings`.
For details see section :doc:`USAGE`. The modules are located in different packages.
In the following a short description of each module.


:mod:`server` Package
---------------------
|

- :mod:`~server.queue_manager` module
    manages the tasks and communication between all other modules via tcp. It is based on Python's
    :class:`multiprocessing.managers.BaseManager`

- :mod:`~server.web` module
    provides an minimal web server which handles incoming user requests from the web frontend.

|
|

:mod:`worker` Package
---------------------
|

- :mod:`~worker.input_worker` module
    fetches every month the top 1 million domains from Alexa,
    prepares them and puts them to the :class:`~server.queue_manager.QueueManager`.

- :mod:`~worker.sslyze_worker` module
    getting domains from the :class:`~server.queue_manager.QueueManager`, analyze the TLS configuration of the servers
    and putting results back to the manager.

- :mod:`~worker.result_worker` module
    getting sslyze results from the :class:`~server.queue_manager.QueueManager`, format it and make it persistent.

|
|

:mod:`helper` Package
---------------------
|

- :mod:`~helper.status` module
    this module prints current status of the scan process. It can be used standalone to get the status if other
    processes running in the background. By default it will be started by hotcat.py, but it can be changed in
    :mod:`settings`.

    if all modules are started, then you can run::

            $ python helper/status.py

    to get current status of the scan process.

- :mod:`~helper.dumper` module
    this module is used by the :class:`~server.queue_manager.QueueManager` to periodically dump the state.
    The :class:`~server.queue_manager.QueueManager` can use the dump to restore the state next time.

- :mod:`~helper.cipher_desc` module
    this holds the cipher description of each cipher string. It is used by the :class:`~worker.result_worker`
    to get the cipher description by given cipher name.

|
|
|
| Lets see the graph:
|
|


.. figure::  _static/schema.png


