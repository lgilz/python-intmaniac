#!/usr/bin/env python

from intmaniac.defaults import *

import os
import os.path
import functools
import subprocess as sp
import logging as log
import sys
from random import randint


python_version = 10 * sys.version_info[0] + sys.version_info[1]
debug = False


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


class DummyCompletedProcess:
    """Poor man's Pyton 2.7 CompletedProcess replacement"""

    # same signature as original class
    def __init__(self, args, returncode, stdout=None, stderr=None):
        # mimic constructor and behavior of CalledProcessError
        self.args = args
        self.returncode = returncode
        self.output = stdout
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        return "<DummyCompletedProcess: %s (%d)" % \
               (" ".join(self.args), self.returncode)


def _construct_return_object(returncode, args, stdout, stderr=None):
    if returncode == 0:
        cls = sp.CompletedProcess \
            if python_version >= 35 \
            else DummyCompletedProcess
        rv = cls(args, returncode, stdout, stderr)
    else:
        rv = sp.CalledProcessError(returncode, args, stdout)
        if not hasattr(rv, "stdout"):
            rv.stdout = rv.output
    return rv


def run_command(command, *args, **kwargs):
    """takes an array as "command", which is executed. Mimics python 3
    behavior, in the way that it returns a CalledProcessError on execution
    failure. The object WILL HAVE the python 3 .stdout and .stderr
    properties, always.
    :param command an array to execute as one command
    :returns a (Dummy)CompletedProcess or CalledProcessError instance, making
     sure all of them have the .stdout, .stderr, .args and .returncode
     properties.
    """
    try:
        p = sp.Popen(command, *args, stdout=sp.PIPE, stderr=sp.STDOUT, **kwargs)
        stdout, _ = p.communicate()
        # we want an exception on failed commands, yes?
        rv = _construct_return_object(p.returncode, command, stdout)
        if type(rv) == sp.CalledProcessError:
            raise rv
    except OSError as err:
        # python 2 & 3, make this behave consistently
        # has .returncode, command and output properties and constructor
        # parameters, but we also need stdout
        rv = sp.CalledProcessError(-7, command, "Exception: " + str(err))
        rv.args = rv.cmd
        rv.stdout = rv.output
        rv.stderr = None
        raise rv
    return rv


##############################################################################
#                                                                            #
# debugging helpers - some things (like file creation & access) are unwanted #
# during debug runs                                                          #
#                                                                            #
##############################################################################


def setup_up_test_directory(config):
    my_id = str(randint(0, 99999)).zfill(5)
    if debug:
        td = "/tmp/intmaniac_00001"
    else:
        td = os.path.join(os.getcwd(), "intmaniac_%s" % my_id) \
            if not config.temp_output_dir \
            else config.temp_output_dir
        if not os.path.isdir(td):
            try:
                os.makedirs(td)
            except IOError:
                fail("Error creating test base directory '%s'" % td)
    return td


def dbg_tr_get_testdir(basedir, testname):
    """If the docker cleanup fails, then we will not have the same names in
    the next run (in which case docker-compose fails). That's why we do prefix
    the test directories with the PID.
    :param basedir the base directory in which the test dirs should be created
    :param testname the name of the test, already sanitized
    :returns a string containing the final path for the docker-compose.yml
    template."""
    prefix = '' if debug else 'p'+str(os.getpid())
    testdir = os.path.join(basedir, prefix + testname)
    return testdir


def enable_debug():
    global debug
    debug = True


if __name__ == "__main__":
    print("Don't do this :)")