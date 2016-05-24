#!/usr/bin/env python

from intmaniac.defaults import *

import functools
import subprocess as sp
import logging as log
import sys


python_version = 10 * sys.version_info[0] + sys.version_info[1]
debug = False

loggercache = {}


##############################################################################
#                                                                            #
# generic helpers                                                            #
#                                                                            #
##############################################################################


def fail(errormessage):
    print("FATAL: %s" % errormessage)
    sys.exit(-10)


def get_test_stub():
    return {'meta': {}, 'environment': {}}


def get_full_stub():
    return {'version': '1.0', 'global': get_test_stub(), 'testsets': {}}


##############################################################################
#                                                                            #
# helper functions for setting up logging                                    #
#                                                                            #
##############################################################################


loglevels = [log.CRITICAL*2, log.CRITICAL, log.ERROR, log.WARNING, log.INFO, log.DEBUG]
global_log_level = -1


def init_logging(config):
    """:param config the configuration object from argparse"""
    global global_log_level
    global_log_level = loglevels[min(len(loglevels)-1, config.verbose)]
    log.basicConfig(
        level=global_log_level,
        format=LOG_FORMAT_CONSOLE,
    )


def get_logger(name, level=-1, filename=None):
    global loggercache
    if name in loggercache:
        return loggercache[name]
    # create new logger
    logger = log.getLogger(name)
    # process all messages
    logger.setLevel(-1)
    logger.propagate = False
    # add a stream handler for console logging in any case.
    # that will be configured with global log level or the log level from the
    # parameter
    handler = log.StreamHandler()
    handler.setLevel(level if level > -1 else global_log_level)
    logger.addHandler(handler)
    # if filename is given, add a stream handler which handles ALL log messages
    # and writes them into a file
    if filename and not debug:
        formatter = log.Formatter(fmt=LOG_FORMAT_FILEOUT)
        handler = log.FileHandler(filename=filename, mode="w")
        handler.setFormatter(formatter)
        handler.setLevel(0)
        logger.addHandler(handler)
    loggercache[name] = logger
    return logger


##############################################################################
#                                                                            #
# logging helper class just for this module                                  #
#                                                                            #
##############################################################################


class Toolslogger:

    logger = None

    @staticmethod
    def get():
        if not Toolslogger.logger:
            Toolslogger.logger = get_logger(__name__)
        return Toolslogger.logger


##############################################################################
#                                                                            #
# deep merge two dicts, the rightmost has preference                         #
#                                                                            #
##############################################################################


def _deep_merge(d0, d1):
    d = {}
    for k, v in d1.items():
        if type(v) == dict and k in d0 and type(d0[k]) == dict:
                d[k] = deep_merge(d0[k], v)
        else:
            d[k] = v
    for k, v in d0.items():
        if k not in d1:
            d[k] = v
    return d


def deep_merge(*args):
    return functools.reduce(_deep_merge, args, {})


##############################################################################
#                                                                            #
# recursive replace - goes through a dict recursively, and performs a string #
# search and replace on all string values, including arrays.                 #
#                                                                            #
##############################################################################

def recursive_replace(struct, search, replace):
    """
    Goes through the dict 'struct' and looks for the string $search in all
    keys and values, including arrays. If found it will replace the string
    :param struct: Either a dictionary, or a list
    :param search: The string to look for
    :param replace: The replacement
    :return: The modified dict
    """
    if isinstance(struct, dict):
        nd = {}
        for k, v in struct.items():
            if isinstance(v, str):
                nd[k] = v.replace(search, replace)
            elif isinstance(v, list) or isinstance(v, dict):
                nd[k] = recursive_replace(v, search, replace)
            else:
                nd[k] = v
        return nd
    elif isinstance(struct, list):
        nl = [
            s.replace(search, replace)
            if isinstance(s, str)
            else s
            for s in struct
        ]
        return nl
    else:
        raise ValueError("Only list and array data types are accepted here")


##############################################################################
#                                                                            #
# a couple of string helpers (py2 vs py3)                                    #
#                                                                            #
##############################################################################


def destr(sob):
    """Will detect if a parameter is a str of bytes data type and decode (in
    case of bytes) or just use it (in case of str)
    :param sob a bytes or string object"""
    # "sob" means "string or bytes"
    tmp = sob.decode("utf-8") if type(sob) == bytes else sob
    return tmp.strip()


##############################################################################
#                                                                            #
# python 2, <3.5 and 3.5+ "subprocess.run() / popen.run()" handler           #
# with unified behavior                                                      #
#                                                                            #
##############################################################################

class RunCommandError(Exception):
    def __init__(self,
                 stdout=None, stderr=None,
                 returncode=256,
                 command=None,
                 exception=None):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.command = command
        self.rv = (command, returncode, stdout, stderr)


def run_command(command, throw=False, expect_returncode=0, **kwargs):
    """
    Executes a command without using popen and returns a tuple with resulting
    information. OSError exceptions are not catched or filtered.
    :param command: An array to execute as one command
    :param throw: If set to True a RunCommandError is raised on an execution
    with error_code not equal to expect_returncode.
    :param expect_returncode: The execution return code to expect when checking
    for successful execution (in case of throw == True)
    :returns A tuple containing (command, returncode, stdout, stderr).
    """
    logger = get_logger(__name__+".run_command")
    p = sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE, **kwargs)
    stdout, stderr = p.communicate()
    stdout_str, stderr_str = destr(stdout), destr(stderr)
    rv = (command, p.returncode, stdout_str, stderr_str)
    _run_command_log(logger.error, logger.debug, rv)
    if throw and rv[1] != expect_returncode:
        ex = RunCommandError(command=command, returncode=p.returncode,
                              stdout=stdout_str, stderr=stderr_str)
        ex.rv = rv
        raise ex
    return rv


def _run_command_log(logger_error_func,
                     logger_normal_func,
                     rv, text=None, expected_returncode=0):
    logger_func = None
    state = text if text else "RUN COMMAND"
    if rv[1] != expected_returncode and logger_error_func is not None:
        logger_func = logger_error_func
        state += " ERROR"
    elif rv[1] == expected_returncode and logger_normal_func is not None:
        logger_func = logger_normal_func
    if logger_func:
        command = rv[0] if isinstance(rv[0], str) else " ".join(rv[0])
        _, retval, stdout, stderr = rv
        err = "{}: '{}' returned {}"\
            .format(state, command, retval)
        if stdout != "":
            err += "\nSTDOUT\n{}".format(stdout)
        if stderr != "":
            err += "\nSTDERR\n{}".format(stderr)
        logger_func(err)


if __name__ == "__main__":
    print("Don't do this :)")
