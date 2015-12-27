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
from threading import Lock, Condition
import settings
from time import time

try:
    from queue import Queue, Empty
    import cPickle, os
except ImportError:
    from Queue import Queue, Empty
    import cPickle, os


class QueueManager(object):
    """
    This class holds and manage all queues.

        .. note::

            Do not use this class directly.
            Instead use :class:`~queue_manager.QueueClient` to connect to the :class:`~queue_manager.QueueServer`
            and get an instance of this class.
    """
    def __init__(self):
        # Location where the dumpfile will be created
        self._dump_location = '../data/queue.dmp'

        # Threshold value describing intervals in which dumps will be created
        self._dump_threshold = 500

        # Threshold for result_queue size
        self._result_queue_threshold = 500

        # Init queues
        self._host_queue = Queue()
        self._user_queue = Queue()
        self._user_result_queue = Queue()
        self._result_queue = Queue()

        self._user_result_dict = {}
        self._host_source_dict = {}

        self._counter = 0
        self._new_list_holder = None
        self._current_list_holder = None

        # Initial value of -1 is preventing getting trapped in the put_new_list function on startup
        self._times_fully_parsed = -1

        # Definitions for Mutex-locks
        self._is_filling = False
        self._filling_condition = Condition()

        # used for measurements
        self._result_counter = 1
        self._start_time = time()

        # Check if dump file exists
        self.read_dump()

    def __call__(self, *args, **kwargs):
        return self

    def create_dump(self):
        """
        Function creates a dump of the current_list_holder and counter variable in data directory
        First the counter variable is pickled, current_list_holder is pickled last.
        """
        print("creating dump at count: "+str(self._counter))
        try:
            dumpFile = open(self._dump_location,'w+b')
            try:
                cPickle.dump(self._counter, dumpFile, cPickle.HIGHEST_PROTOCOL)
                cPickle.dump(self._current_list_holder, dumpFile, cPickle.HIGHEST_PROTOCOL)
            except (cPickle.PickleError,cPickle.PicklingError) as pe:
                print pe
            finally:
                dumpFile.close()
        except OSError as oe:
                    print(oe)



    def read_dump(self):
        """
        Function will look for a dump file in Data directory, read it and
        initialize the host_queue in queue_manager accordingly
            .. note::
                This function assumes that counter variable has been pickled first and the
                list representing the host_queue last.
        """
        if os.path.exists(self._dump_location):
            print("Found dump file.")
            try:
                fileIn = open(self._dump_location,'rb')
                try:
                    lastCounter = cPickle.load(fileIn)
                    self._current_list_holder = cPickle.load(fileIn)
                    print("Last iteration stopped at entry: "+str(lastCounter)+": "+str(self._current_list_holder[lastCounter]))
                    if(lastCounter != 0):
                        # Create a list in which already scanned URLs are appended at the end of the list
                        tempList = self._current_list_holder[lastCounter : ]+self._current_list_holder[0 : lastCounter]
                        self._current_list_holder = tempList
                    self.put_new_list(self._current_list_holder)

                except (cPickle.UnpicklingError, cPickle.UnpicklingError) as pe:
                    print(pe)
                finally:
                    fileIn.close()
            except OSError as oe:
                print(oe)
        else:
            print("No dump file found. Continuing with regular operation")
            return



    def next_host(self):
        """
        Getting next hostname from the appropriate queue.

        :return str: hostname e.g. "google.com"
        """
        if (self._counter % self._dump_threshold == 0):
            self.create_dump()

        if self._result_queue.qsize() >= self._result_queue_threshold:
            print("result_queue full, check if result_worker is running")
            return None, None

        if not self._user_queue.empty():
            # Trap for prioritizing the user_queue
            return self._user_queue.get()

        try:
            hostname = self._host_queue.get(timeout=3)
        except Empty:
            return None, None

        with self._filling_condition:
            while self._is_filling:
                self._filling_condition.wait()

            # cycle queue
            self._host_queue.put(hostname)

            self.put_new_list(self._new_list_holder)

            # keep track by counting
            self._counter += 1

            # Keep track of how many times the host_queue has been "parsed" by sslyze
            if self._counter == len(self._host_queue.queue):
                self._counter = 0
                self._times_fully_parsed +=1

            #print("The position counter:", self._counter," Times fully parsed: ",self._times_fully_parsed)
            return hostname, None

    def empty_queue(self):
        """
        Empty entire queue.
            .. note::

                *use this function with care*. it will empty the whole host_queue.
                even if the host_queue has not finished yet.
        """
        self._counter = 0
        self._host_source_dict = {}

        while not self._host_queue.empty():
            self._host_queue.get()

    def put_user(self, user_request, user_id):
        """
        Function will store any user requested urls to _user_queue
        and ready the _user_result_dict for an incoming sslyze result
        corresponding to user_id

        :param list user_request: the url requested to be checked by sslyze
        :param user_id: unique user identifier corresponding to the request
        """
        self._user_result_dict[user_id] = Queue()
        self._user_queue.put((user_request, user_id))

    def put_new_list(self, new_list):
        """
        Empty and refill the queue.

        :param list new_list: nested list with hostname and source e.g. [ ["google.com", ["alexa-top-1m", ] ], ]
        """

        self._new_list_holder = new_list

        # if no list has been supplied, leave method and continue
        if not self._new_list_holder:
            return

        # Trap if sslyze is working the list for the fist time or is in the middle of working it the n-th time
        if self._counter > 0 or self._times_fully_parsed == 0:
            return

        print("adding new list ...")
        # indicates that the queue will be filled currently
        self._is_filling = True

        self.empty_queue()  # self_counter is reset to 0 in here

        for i, item in enumerate(new_list):
            if (i % 10000) == 0 and i > 0:
                print("%s domains added" % i)
            self._host_source_dict[item[0]] = item[1]
            self._host_queue.put(item[0])

        print("new list was added")

        self._times_fully_parsed = 0
        self._current_list_holder = self._new_list_holder
        self._new_list_holder = None
        self._is_filling = False

        with self._filling_condition:
            self._filling_condition.notify_all()

    def next_result(self):
        """
        Getting next result from result_queue.

        :return tuple: ({sslyze result}, [source,])
        """
        res = self._result_queue.get()
        target = res["target"]
        res["source"] = self._host_source_dict[target[0]]
        return res

    def get_user_result(self, user_id):
        """
        Function will get and return the result
        corresponding to the supplied user_id

        :param user_id: the user_id to identify which result to get
        :return: the sslyze result

        .. note::   _inner_result_queue is a local field and will not be available beyond
                    this function
                    There will be only one sslyze result per user_id
        """
        try:
            result = self._user_result_dict[user_id].get(30)
        except Empty:
            result = dict(error="internal timeout")

        del self._user_result_dict[user_id]

        return result

    def put_result(self, result):
        """
        Adding a result to result_queue.
        :param result: the sslyze result to pe added to the _result.queue
        """
        if self._result_counter == 1:
            self._start_time = time()

        exec_time = time() - self._start_time

        print("#"*50)
        print('scan completed for target:     %s' % result.get("target")[0])
        print('total scans completed:         %s' % self._result_counter)
        print('average scan time per target: {0:.2f} s'.format(exec_time/self._result_counter))
        print('total scan time: {0:.2f} m'.format(exec_time/60))
        print('result_queue size: %s' % self._result_queue.qsize())
        print("#"*50)

        self._result_counter += 1
        self._result_queue.put(result)

    def put_user_result(self, result, user_id):
        """
        Function will will add an sslyze result to the _user_result_dict
        :param result: the sslyze result to be added
        :param user_id: the user identifier for the corresponding result
        .. note::   _inner_result_queue is a local field and will not be available beyond
                    this function
                    There will be only one sslyze result per user_id
        """
        _inner_result_queue = self._user_result_dict[user_id]
        _inner_result_queue.put(result)


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
        queue_manager = c.queue_manager()

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