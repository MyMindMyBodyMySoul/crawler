"""
This module starts all required worker processes in the correct order.
Just run:
    ::

        $ python hft_tls_crawler.py
"""

import os
import sys
import signal
from datetime import datetime
import subprocess
from threading import Thread
from Queue import Queue

import settings

#: the path to your python executable
PYTHON_PATH = ""

#: all modules in this list will be started in separate process
MODULE_LIST = ["queue_manager.py", "myinput_worker.py", "sslyze_worker.py", "result_worker.py"]

#: the output of the modules in this list will be logged to console or to file
LOG_MODULES = MODULE_LIST

#: holds the running processes
RUNNING_PROCESSES = []



def _enqueue_out(stream, module, q):
    """
    iterate over each line in stdout and put line to queue.

    :param stream: the stream of stdout
    :param module: the name of the module to keep track of stdout
    :param q: the queue to put each line
    :return:
    """
    for line in iter(stream.readline, b''):
        q.put((module, "stdout", line.rstrip(b'\r\n')))


def _enqueue_err(stream, module, q):
    """
    iterate over each line in stderr and put line to queue.

    :param stream: the stream of stderr
    :param module: the name of the module to keep track of stderr
    :param q: the queue to put each line
    :return:
    """
    for line in iter(stream.readline, b''):
        q.put((module, "stderr", line.rstrip(b'\r\n')))


def _sigint_handler(signum, frame):
    """
    handles keyboard interrupt
    :param signum:
    :param frame:
    :return:
    """
    print("### TERMINATION ###")
    for p, module in RUNNING_PROCESSES:
        print("terminating %s with PID %s)" % (module, p.pid))
        p.terminate()
        p.wait()
    sys.exit()


def _to_console(fd, module, pipe_type, msg, ts):
    if pipe_type == "stderr":
        color = 95
    elif module == "queue_manager.py":
        color = 91
    elif module == "input_worker.py":
        color = 94
    elif module == "sslyze_worker.py":
        color = 92
    elif module == "result_worker.py":
        color = 93

    msg = "\033[%sm%s [%s]:     %s\033[0m\n" % (color, ts, module, msg)
    fd.write(msg)


def _to_file(fd, module, pipe_type, msg, ts):
    msg = "%s [%s]:     %s\n" % (ts, module, msg)
    fd.write(msg)


def main():
    """
    Starts all modules which are listed in :data:`~hft_tls_crawler.MODULE_LIST`.
    """

    signal.signal(signal.SIGINT, _sigint_handler)

    q = Queue()

    print("Starting modules ...")

    for module in MODULE_LIST:

        p = subprocess.Popen([os.path.join(PYTHON_PATH, "python"), "-u", module], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        RUNNING_PROCESSES.append([p, module])

        print("%s is running with PID %s" % (module, p.pid))

        t = Thread(target=_enqueue_out, args=(p.stdout, module, q))
        t.daemon = True  # thread dies with the program
        t.start()

        t = Thread(target=_enqueue_err, args=(p.stderr, module, q))
        t.daemon = True  # thread dies with the program
        t.start()

    print("")

    #the FD in which is written.
    if settings.LOG_FILE:
        log_fd = open(settings.LOG_FILE, "w")
        _write_log = _to_file
    else:
        log_fd = sys.stdout
        _write_log = _to_console

    while True:
        line = q.get()

        if line[0] in LOG_MODULES:
                _write_log(log_fd, line[0], line[1], line[2], str(datetime.now()).split('.')[0])


if __name__ == "__main__":
    main()
