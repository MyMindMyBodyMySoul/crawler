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
    from sslyze.utils.ServersConnectivityTester import ServersConnectivityTester, InvalidTargetError
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
    def __init__(self, qm, available_commands):
        Process.__init__(self)

        self._qm = qm
        self.available_commands = available_commands

    def run(self):
        # Plugin classes are unpickled by the multiprocessing module
        # without state info. Need to assign shared_settings here

        for plugin_class in self.available_commands.itervalues():
            plugin_class._shared_settings = settings.SHARED_SETTINGS

        hostname, user_id = self._qm.next_host()

        if hostname is None:
            return

        target = self._test_server(hostname)

        if target[0]:
            result_dict = dict(target=target, result=[], error=False)

            for command in settings.COMMAND_LIST:
                result = self._process_command(target, command)
                result_dict["result"].append(self._check_result(command, result))

        else:
            result_dict = target[1]

        if user_id:
            self._qm.put_user_result(result_dict, user_id)
        else:
            self._qm.put_result(result_dict)

    def _check_result(self, command, result):
        from plugins.PluginBase import PluginResult

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

        return result

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

    # PLUGINS INITIALIZATION
    sslyze_plugins = PluginsFinder()
    available_commands = sslyze_plugins.get_commands()

    # QUEUE INITIALIZATION
    c = QueueClient()
    qm = c.queue_manager()

    # PROCESS INITIALIZATION
    while True:

        p = WorkerProcess(qm, available_commands)
        p.start()
        process_list.append(p)

        # Wait for processes to terminate
        p.join()

if __name__ == "__main__":
    main()

