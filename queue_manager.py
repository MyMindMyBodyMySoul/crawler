"""
This module contains following classes:
:class:`~queue_manager.QueueManager`,
:class:`~queue_manager.QueueClient`,
:class:`~queue_manager.QueueServer`.

You can run this module directly to start the server.
The server bind to address and port, which are specified in :mod:`settings`.
    ::

        $ python queue_manager.py
"""

from multiprocessing.managers import BaseManager
import settings

try:
    from queue import Queue
except ImportError:
    from Queue import Queue


class QueueManager(object):
    """
    This class holds and manage all queues.

        .. note::

            Do not use this class directly.
            Instead use :class:`~queue_manager.QueueClient` to connect to the :class:`~queue_manager.QueueServer`
            and get an instance of this class.
    """
    def __init__(self):
        self._host_queue = Queue()
        self._user_queue = Queue()
        self._result_queue = Queue()

        self._host_source_dict = {}

        self._counter = 0

    def __call__(self, *args, **kwargs):
        return self

    def next_host(self):
        """
        Getting next hostname of the appropriate queue.

        :return str: hostname e.g. "google.com"
        """
        if not self._user_queue.empty():
            return self._user_queue.get()

        # cycle queue and keep track by counting
        hostname = self._host_queue.get()

        if hostname is None:
            return

        self._host_queue.put(hostname)
        self._counter += 1
        return hostname

    def empty_queue(self):
        """
        Empty entire queue.
            .. note::

                *use this function with care*. it will empty the whole host_queue.
                even if the host_queue has not finished yet.
        """
        # two possibilities: emptying with a loop or garbage collection
        self._counter = 0
        self._host_source_dict = {}
        self._host_queue.put(None)
        self._host_queue = Queue()

    def put_user_list(self, user_list):
        """

        :param list user_list:
        :return:
        """
        # TODO
        pass

    def put_new_list(self, new_list):
        """
        Empty and refill the queue.

        :param list new_list: nested list with hostname and source e.g. [ ["google.com", ["alexa-top-1m", ] ], ]
        """
        # queue is not even through ?
        if len(self._host_queue.queue) > self._counter:
            return

        print("adding new list ...")
        self.empty_queue()
        for item in new_list:
            self._host_source_dict[item[0]] = item[1]
            self._host_queue.put(item[0])

        print("new list was added")


    def next_result(self):
        """
        Getting next result from result_queue.

        :return tuple: ({sslyze result}, [source,])
        """
        res = self._result_queue.get()
        target = res["target"]
        res["source"] = self._host_source_dict[target[0]]
        return res

    def put_result(self, result):
        """
        Putting result to result_queue.

        :param result:
        :return:
        """
        self._result_queue.put(result)


class QueueClient(BaseManager):
    """
    This class is used to connect to QueueServer.

    If you instantiate this class it will auto connect to the server.
    So you can get an instance by name of each registered object.

    :Example:

    ::

        from queue_manager import QueueClient

        c = QueueClient()

        # registered name is "queue_manager" , so you can call it to get
        # the instance of QueueManager class.
        queue_manager = c.queue_manger()

        # do something with queue_manager ...

    """
    def __init__(self, address=(settings.SERVER_ADDRESS, settings.SERVER_PORT),
                 authkey=settings.SERVER_AUTH):

        self.register('queue_manager')
        BaseManager.__init__(self, address=address, authkey=authkey)
        self.connect()


class QueueServer(BaseManager):
    """
    The QueueServer ...
    """
    def __init__(self):
        self.register('queue_manager', callable=QueueManager())
        BaseManager.__init__(self, address=(settings.SERVER_ADDRESS, settings.SERVER_PORT),
                             authkey=settings.SERVER_AUTH)


if __name__ == "__main__":
    m = QueueServer()
    s = m.get_server()
    print("starting QueueServer at %s:%s" % (settings.SERVER_ADDRESS, settings.SERVER_PORT))
    s.serve_forever()