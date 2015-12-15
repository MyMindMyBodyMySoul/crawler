"""
This worker analyzes hosts similarly to how SSLyze does.
"""

__author__ = ["David Hoeyng", "Adrian Zapletal"]
__license__ = ""  # TODO ?
__version__ = "0.1"

import sys
import signal
from multiprocessing import Process
import settings
from server.queue_manager import QueueClient
from sslyze.plugins import PluginsFinder

try:
    from utils.ServersConnectivityTester import ServersConnectivityTester, InvalidTargetError
except ImportError as e:
    print str(e) + '\nERROR: Could not import nassl Python module. Did you clone SSLyze\'s repo ? \n' +\
    'Please download the right pre-compiled package as described in the README.\n'
    sys.exit()

# Global so we can terminate processes when catching SIGINT
process_list = []


class WorkerProcess(Process):
    """
    This class checks hosts from the host_queue with the settings specified in settings.py.
    """
    def __init__(self, qm, available_commands, i):
        Process.__init__(self)

        self._qm = qm
        self.available_commands = available_commands
        self._i = i

    def run(self):
        # Plugin classes are unpickled by the multiprocessing module
        # without state info. Need to assign shared_settings here
        from plugins.PluginBase import PluginResult
        for plugin_class in self.available_commands.itervalues():
            plugin_class._shared_settings = settings.SHARED_SETTINGS

        while True:

            hostname, user_id = self._qm.next_host()

            if user_id:
                print("process %s got hostname: %s" % (self._i, hostname))

            if hostname is None:
                continue

            target = self._test_server(hostname)

            if target[0]:
                result_dict = dict(target=target, result=[], error=False)

                for command in settings.COMMAND_LIST:
                    result = self._process_command(target, command)

                    if isinstance(result, PluginResult):
                        result = result.get_raw_result()
                        if result:
                            result["command"] = command
                            result["error"] = False
                        else:
                            result = dict(command=command, error=True, err_msg="command is not supported")

                    elif isinstance(result, str):
                        result = dict(command=command, error=True, err_msg=result)

                    else:
                        result = dict(command=command, error=True, err_msg="command is not supported")

                    result_dict["result"].append(result)

            else:
                result_dict = target[1]

            if user_id:
                self._qm.put_user_result(result_dict, user_id)
            else:
                self._qm.put_result(result_dict)

    def _process_command(self, target, command):
            plugin_instance = self.available_commands[command]()
            try:  # Process the task
                result = plugin_instance.process_task(target, command, "basic")
            except Exception as err:  # Generate txt and xml results
                result = err  # TODO format exception
            return result

    def _test_server(self, hostname):
        try:
            target = ServersConnectivityTester._test_server(hostname, settings.SHARED_SETTINGS)
        except InvalidTargetError as err:
            result_dict = dict(target=(hostname, None, None), result=err.get_error(), error=True)
            return None, result_dict
        return target


def _sigint_handler(signum, frame):
    for p in process_list:
        p.terminate()
    sys.exit()


def main():
    """
    Starts as many sslyze worker processes as specified in :mod:`settings`.
    """

    signal.signal(signal.SIGINT, _sigint_handler)

    ##########################
    # PLUGINS INITIALIZATION #
    ##########################
    sslyze_plugins = PluginsFinder()
    available_plugins = sslyze_plugins.get_plugins()
    available_commands = sslyze_plugins.get_commands()

    ########################
    # QUEUE INITIALIZATION #
    ########################
    print("connect to QueueManager ...")

    c = QueueClient()
    qm = c.queue_manager()

    ##########################
    # PROCESS INITIALIZATION #
    ##########################
    print("starting %s sslyze worker processes ..." % settings.NUMBER_PROCESSES)

    for _ in xrange(settings.NUMBER_PROCESSES):
        p = WorkerProcess(qm, available_commands, _)
        p.start()
        process_list.append(p)

    # Wait for all processes to terminate
    for p in process_list:
        p.join()


if __name__ == "__main__":
    main()
