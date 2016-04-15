from intmaniac.testrun import Testrun
from intmaniac.tools import fail, deep_merge, get_logger

import yaml

import tempfile
from re import search as research
from os import write as fdwrite, close as fdclose
from os.path import dirname, join, isabs


logger = get_logger(__name__)


def parse(argconfig):
    """
    Opens the configuration file, de-serializes the contents, checks the
    version number, and gives the configuration to the actual parser function.
    Will return whatever the parser function returns, which should be a list
    of Testrun objects.
    :param path_to_file: The path to the configuration file
    :return: A list of Testrun objects (hopefully :)
    """
    path_to_file = argconfig.config_file
    with open(path_to_file, "r") as infile:
        fileconfig = yaml.safe_load(infile)

    if 'version' not in fileconfig:
        fail("Need 'config' key in configuration file, must be '2'.")
    else:
        conf_version = str(fileconfig['version'])
        if conf_version == '1':
            fail("This version only uses version '2' config files!")
        if conf_version == '2':
            return _parsev2(fileconfig, argconfig)
        else:
            fail("Unknown config file version: '{}'. "
                 "Must be: <absent>, '1' or '2'".format(conf_version))


#  #########################################################################  #
#                                                                             #
#  Configuration v2                                                           #
#                                                                             #
#  #########################################################################  #

def _parsev2(fileconfig, argconfig):
    """
    Reads and understands the intmaniac configuration file (v2), and returns
    the Testrun objects.
    :param fileconfig: The de-serialized configuration as dict object
    :param argconfig: The global config object from the command line params.
    :return: A list of Testrun objects
    """
    # first, check for missing keys.
    # we need:
    #   - version
    #   - compose_template
    #   - tester_image
    needed_keys = [
        'compose_template',
        'tester_config',
    ]
    errors = []
    for key in needed_keys:
        if key not in fileconfig:
            errors.append("CONFIG FILE: missing key '{}'".format(key))
    if not isinstance(fileconfig['compose_template'], str):
        errors.append("CONFIG FILE: 'compose_template' key must have "
                      "a string value")
    if len(errors):
        fail("\n" + "\n".join(errors))
    # prepare the path to the docker-compose template
    if not isabs(fileconfig['compose_template']):
        fileconfig['compose_template'] = join(dirname(argconfig.config_file),
                                              fileconfig['compose_template'])
    tester = _prepare_tester_config(fileconfig['tester_config'], argconfig)
    compose = _prepare_docker_compose_template(fileconfig['compose_template'],
                                               tester['environment'],
                                               argconfig)
    # now, create the test run object
    tr = Testrun('default', compose, **tester)
    return [tr]


def _prepare_tester_config(tester_config, global_config, more_envs={}):
    """
    Validates the tester_config structure. Basically checks for presence of
    'image' key. Then it will make sure that all keys are present, with the
    correct types. The environment values in global_config have precedence
    above all else.
    :param tester_config: The tester_config structure
    :param global_config: The global configuration from the command line
    :param more_envs: more key-value items to merge into the environment
    :return: None
    """
    tester_template = {
        'environment': {},
        'links': {},
        'commands': [],
    }
    errors = []
    if 'image' not in tester_config or \
            not isinstance(tester_config['image'], str):
        errors.append("tester_config key must contain 'image' key "
                      "and must be a string")
    if 'links' not in tester_config or \
            not isinstance(tester_config['links'], list):
        errors.append("tester_config key must contain 'links' key"
                      " as array")
    if len(errors):
        fail("\n" + "\n".join(errors))
    tmp = deep_merge(tester_template, tester_config)
    tmp['environment'] = deep_merge(tmp['environment'],
                                    more_envs,
                                    global_config.env)
    return tmp


def _prepare_docker_compose_template(compose_file, search_and_replace_dict, gc):
    """
    Reads the docker-compose template and performs the necessary replacements:
    All environment variables from tester_template[environment] will be string-
    searched and -replaced in the form "%%<KEY>%%" -> <value>. The key is
    always upper-cased for search and replace.
    Note that the docker-compose template is never deserialized here, only
    handled as string data to create a temporary docker-compose file.
    :param compose_file: The path to the docker-compose file.
    :param search_and_replace_dict: The dict with the search-and-replace
    information
    :param gc: The global configuration from the command line parameters
    :return: A system file path to a temporary docker-compose template
    """
    try:
        with open(compose_file, "r", encoding='utf-8') as infile:
            data = infile.read()
    except IOError as ex:
        fail("Could not read docker-compose file: {}".format(str(ex)))
    for k, v in search_and_replace_dict.items():
        data = data.replace("%%{}%%".format(k.upper()), v)
    if not gc.force:
        result = research("(%%[A-Z0-9_-]+%%)", data)
        if result:
            fail("found replacement tags in compose file "
                 "(missing env setting?): {}\n"
                 "Ignore with -f setting"
                 .format(", ".join(map(lambda x: "'{}'".format(x),
                                      result.groups()))))
    handle, tmpfile = tempfile.mkstemp()
    fdwrite(handle, data.encode('utf-8'))
    fdclose(handle)
    logger.debug("Created temp compose file {}".format(tmpfile))
    return tmpfile
