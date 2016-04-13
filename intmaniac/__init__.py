#!/usr/bin/env python

import yaml

from intmaniac.testset import Testset
from intmaniac import tools
from intmaniac import output

import sys
from os import getcwd
from os.path import join, realpath
from errno import *
from argparse import ArgumentParser

config = None
logger = None
derived_basedir = None
global_overrides = None


##############################################################################
#                                                                            #
# default configuration values for test config                               #
#                                                                            #
##############################################################################


##############################################################################
#                                                                            #
# reading of config data                                                     #
# initialization of test set objects                                         #
#                                                                            #
##############################################################################


def _get_test_sets(setupdata):
    """Always returns a list of list of Testsets
        :param setupdata the full yaml setup data
    """
    testsets = setupdata['testsets']
    global_config = setupdata['global']
    rv = []
    for tsname, tests in sorted(testsets.items()):
        ts = Testset(name=tsname)
        rv.append(ts)
        # remove global settings from test set
        ts.set_global_config(tools.deep_merge(global_config,
                                              tests.pop("_global", {})))
        for test_name, test_config in sorted(tests.items()):
            # the overrides have precedence above everything
            use_test_config = tools.deep_merge(test_config, global_overrides)
            ts.add_from_config(test_name, use_test_config)
    return rv


def _get_setupdata():
    stub = tools.get_full_stub()
    filedata = None
    try:
        with open(config.config_file, "r") as ifile:
            filedata = yaml.safe_load(ifile)
    except IOError as e:
        # FileNotFoundError is python3 only. yihah.
        if e.errno == ENOENT:
            tools.fail("Could not find configuration file: %s" % config.config_file)
        else:
            tools.fail("Unspecified IO error: %s" % str(e))
    logger.info("Read configuration file %s" % config.config_file)
    return tools.deep_merge(stub, filedata)


def _prepare_overrides():
    global global_overrides
    global_overrides = tools.get_test_stub()
    # add config file entry
    global_overrides['meta']['_configfile'] = config.config_file
    # add test_basedir entry
    global_overrides['meta']['test_basedir'] = derived_basedir
    # add env settings from command line
    for tmp in config.env:
        try:
            k, v = tmp.split("=", 1)
            global_overrides['environment'][k] = v
        except ValueError:
            tools.fail("Invalid environment setting: %s" % tmp)


def _get_and_init_configuration():
    setupdata = _get_setupdata()
    _prepare_overrides()
    if "output_format" in setupdata:
        logger.warning("Text output format: %s" % setupdata['output_format'])
        output.init_output(setupdata['output_format'])
    return setupdata


##############################################################################
#                                                                            #
# run test sets logic                                                        #
#                                                                            #
##############################################################################


def _run_test_sets(testsets):
    retval = True
    dumps = []
    for testset in testsets:
        testset.run()
        retval = testset.succeeded() and retval
        dumps.append(testset.dump)
    output.output.block_open("Test protocol")
    for dump_function in dumps:
        dump_function()
    output.output.block_done()
    return retval


##############################################################################
#                                                                            #
# startup initialization                                                     #
#                                                                            #
##############################################################################


def _prepare_environment(arguments):
    global config, logger, derived_basedir
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
    parser.add_argument("-t", "--temp-output-dir",
                        help="test dir location, default: $pwd/intmaniac/",
                        default=realpath(join(getcwd(), './intmaniac/')))
    config = parser.parse_args(arguments)
    tools.init_logging(config)
    derived_basedir = tools.setup_up_test_directory(config)
    logger = tools.get_logger(__name__,
                              filename=join(derived_basedir, "root.log"))


def _internal_entrypoint(args):
    _prepare_environment(args)
    configuration = _get_and_init_configuration()
    result = _run_test_sets(_get_test_sets(configuration))
    if not result:
        sys.exit(1)


def console_entrypoint():
    _internal_entrypoint(sys.argv[1:])
