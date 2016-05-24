#!/usr/bin/env python

from intmaniac import maniac_file
from intmaniac import tools
from intmaniac import output

import sys
from os import getcwd, unlink
from os.path import join, realpath, isfile
from argparse import ArgumentParser

logger = None


##############################################################################
#                                                                            #
# run test sets logic                                                        #
#                                                                            #
##############################################################################


def _print_test_results(argconfig, test):
    """The information from the test object is as follows:
    - test.name
    - test.test_state
    - test.test_results
    - test.exception
    The test_results member consists of the following information:
    (test_command, return_value, stdout, stderr).
    The .exception member is filled only if an exception occurred internally.
    :param test: the Testrun object to print out
    :return: None"""
    if argconfig.no_format_output:
        if test.exception:
            output.output.dump(str(test.exception))
        for result in test.test_results:
            for num in (2, 3):
                if result[num]:
                    output.output.dump(result[num])
    else:
        output.output.test_open(test.name)
        output.output.message("Test status: {}".format(test.test_state))
        if not test.succeeded():
            output.output.test_failed(type=test.reason,
                                      message=str(test.exception)
                                      if test.exception
                                      else None)
        for num, result in enumerate(test.test_results):
            output.output.block_open("Test command {}".format(num + 1))
            output.output.message("COMMAND: {}".format(" ".join(result[0])))
            if result[2]:
                output.output.block_open("STDOUT")
                output.output.dump(result[2])
                output.output.block_done()
            if result[3]:
                output.output.block_open("STDERR")
                output.output.dump(result[3])
                output.output.block_done()
            output.output.block_done()
        output.output.test_done()


def _run_tests(argconfig, tests):
    re_raise_me = None
    try:
        retval = True
        for test in tests:
            test.run()
            retval = test.succeeded() and retval
            _print_test_results(argconfig, test)
    except Exception as e:
        # this is just to make sure we really kill those darn temp files.
        re_raise_me = e
    finally:
        for test in tests:
            try:
                unlink(test.template)
            finally:
                pass
    if re_raise_me:
        raise re_raise_me
    return retval


##############################################################################
#                                                                            #
# startup initialization                                                     #
#                                                                            #
##############################################################################


def _parse_args(arguments):
    """
    Parses the arguments list given as parameter using argparse. Post-processes
    the configuration data (e.g. converting the string vars containing the
    KEY=VAL values for environment settings to a dict {k:v,...}).
    :param arguments: The argument list to parse
    :return: The config data object
    """
    parser = ArgumentParser()
    parser.add_argument("-c", "--config-file",
                        help="specify configuration file. "
                             "Default: ./intmaniac.yml",
                        default=realpath(join(getcwd(), "intmaniac.yaml")))
    parser.add_argument("-e", "--env",
                        help="dynamically add a value to the environment",
                        action="append",
                        default=[])
    parser.add_argument("-v", "--verbose",
                        help="increase verbosity level, use multiple times",
                        action="count",
                        default=0)
    parser.add_argument("-f", "--force",
                        help="Ignore warnings",
                        action="store_true",
                        default=False)
    parser.add_argument("-o", "--output-type",
                        help="Set output type from ('base', 'teamcity'). "
                             "Default: 'base'",
                        default='base')
    parser.add_argument("--no-format-output",
                        action='store_true',
                        help="If set the output from the executed test "
                             "container is passed through completely "
                             "unfiltered.",
                        default=False)
    config = parser.parse_args(arguments)
    # process arguments
    config.env = dict([e.split("=", 1) for e in config.env])
    return config


def _init_logging(config):
    global logger
    tools.init_logging(config)
    logger = tools.get_logger(__name__)


def _internal_entrypoint(args):
    config = _parse_args(args)
    _init_logging(config)
    output.init_output(config.output_type)
    tests = maniac_file.parse(config)
    result = _run_tests(config, tests)
    if not result:
        sys.exit(255)


# this is for the console invocation by setuptools.
def console_entrypoint():
    _internal_entrypoint(sys.argv[1:])
