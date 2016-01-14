"""
This module contains global settings for all modules.
"""

##########################
# RUNNING                #
##########################

#: the path to your python executable. empty string for default system interpreter.
PYTHON_PATH = ""

#: all modules in this list will be started in separate process.
MODULE_LIST = [
    "server.queue_manager",
    "server.web",
    "worker.input_worker",
    "worker.result_worker",
    "worker.sslyze_worker",
    "helper.status"
]


##########################
# LOGGING                #
##########################

#: the output of the modules in this list will be logged to console or to file.
LOG_MODULES = MODULE_LIST

#: the file in which all output will be written. If None it goes to stdout.
LOG_FILE = None


##########################
# SERVER                 #
##########################

#: the bind address of the :mod:`~server.web`.
WEB_SERVER_ADDRESS = 'localhost'

#: the bind port of the :mod:`~server.web`.
WEB_SERVER_PORT = 50002

#: the bind address of the :class:`~server.queue_manager.QueueServer`.
SERVER_ADDRESS = 'localhost'

#: the bind port of the :class:`~server.queue_manager.QueueServer`.
SERVER_PORT = 50001

#: the authentication string of the :class:`~server.queue_manager.QueueServer`.
SERVER_AUTH = b'abc'


##########################
# SSLYZE                 #
##########################

#: the number of sslyze worker processes
NUMBER_PROCESSES = 2

#: a list of commands that sslyze will be used for scanning.
#:  available commands are:
#:      ["tlsv1_2", "tlsv1_1", "tlsv1", "sslv3", "sslv2", "reneg", "hsts", "resum", "resum_rate",
#:      "heartbleed", "chrome_sha1", "compression", "certinfo"]
#: For details see `SSLyze <https://github.com/nabla-c0d3/sslyze>`_.
COMMAND_LIST = [
    "tlsv1_2",
    "tlsv1_1",
    "tlsv1",
    "sslv3",
    "sslv2",
    # "reneg",
    # "hsts",
    # "resum",
    # "resum_rate",
    # "heartbleed",
    # "chrome_sha1",
    # "compression",
    "certinfo",
]


#: this are shared settings used by sslyze.
#:   For details see `SSLyze <https://github.com/nabla-c0d3/sslyze>`_.
SHARED_SETTINGS = {
    'ca_file': None,
    'certinfo': 'basic',
    'starttls': None,
    'resum': True,
    'resum_rate': None,
    'http_get': True,
    'xml_file': None,
    'compression': True,
    'tlsv1': True,
    'targets_in': None,
    'keyform': 1,
    'hsts': None,
    'chrome_sha1': None,
    'sslv3': True,
    'sslv2': True,
    'https_tunnel': None,
    'nb_retries': 4,
    'heartbleed': True,
    'sni': None,
    'https_tunnel_host': None,
    'regular': False,
    'key': None,
    'reneg': True,
    'tlsv1_2': True,
    'tlsv1_1': True,
    'hide_rejected_ciphers': True,
    'quiet': None,
    'keypass': '',
    'cert': None,
    'timeout': 5,
    'xmpp_to': None
}





