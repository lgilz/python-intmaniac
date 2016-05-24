#!/usr/bin/env python

from intmaniac.tools import run_command
from intmaniac.tools import get_logger, RunCommandError
from intmaniac.dockhelpers import *

import os
from os.path import basename
from re import sub as resub


def _build_exec_array(base=None):
    """Will return a list containing lists containing words. Each inner list
       is a single command to execute, which is split into words.
       Example: [ ["sleep", "10"], [ "echo", "hi"] ]
    """
    if not base:
        return []
    if isinstance(base, str):
        return [base.split(" ")]
    elif isinstance(base, list) or isinstance(base, tuple):
        tmp = list(base)
        tmp = [item.split(" ")
               if isinstance(item, str) else item for item in tmp]
        return tmp
    else:
        raise ValueError("Can't construct command array out of this: %s" %
                         str(base))


class Testrun(object):
    """Actually invokes docker-compose with the information given in the
    configuration, and evaluates the results.
    """

    NOTRUN = "NOTRUN"
    SUCCEEDED = "SUCCEEDED"
    CONTROLLED_FAILURE = "ALLOWED_FAILURE"
    FAILURE = "FAILED"

    def __init__(self,
                 name,
                 compose_file,
                 **kwargs):
        self.name = "{}".format(name if name else basename(compose_file))
        self.sanitized_name = "intmaniac{}".format(
            resub("[^a-z0-9]", "",
                  self.name.lower() + basename(compose_file).lower())
        )
        self.template = compose_file
        self.compose_wrapper = Compose(compose_file, self.sanitized_name,
                                       run_kwargs={'throw': True})
        # extract "top level" parameters
        self.test_env = kwargs.pop('environment', {})
        self.test_image = kwargs.pop('image')
        self.test_linked_services = kwargs.pop('links')
        self.test_commands = _build_exec_array(kwargs.pop('commands', []))
        # save the rest
        self.meta = kwargs
        # state information
        self.test_state = self.NOTRUN
        self.test_results = []
        self.exception = None
        self.reason = None
        # run information - this can only be set after the env is running
        self.cleanup_test_containers = []
        self.run_containers = None
        # log setup
        self.log = get_logger("t-%s" % self.name)
        # some debug output
        self.log.debug("using template '%s'" % self.template)
        for key, val in self.test_env.items():
            self.log.debug("env %s=%s" % (key, val))

    def __str__(self):
        return "<runner.Test '%s' (%s)>" % (self.name, self.test_state)

    def __repr__(self):
        return "%s, state '%s'" % (self.name, self.test_state)

    def __eq__(self, other):
        eq = True
        eq = eq and self.test_env == other.test_env
        eq = eq and self.test_image == other.test_image
        eq = eq and self.template == other.template
        eq = eq and self.test_commands == other.test_commands
        eq = eq and self.test_linked_services == other.test_linked_services
        return eq

    def _container_for_service(self, service_name):
        try:
            return next(filter(lambda x: x[1] == service_name,
                               self.run_containers))[0]
        except StopIteration as ex:
            # we cannot find the service name in the service list
            ex = KeyError("Cannot find service '{}' in started services"
                          .format(service_name))
            raise ex

    def _run_local_commands(self, commands):
        """
        Executes a list of commands on the local machine (pre- and post-
        commands, intendedly.
        :param commands: The commands to execute
        :return: A list with the return objects.
        """
        if not commands:
            return
        rvs = []
        for command in _build_exec_array(commands):
            rvs.append(run_command(command,
                                   throw=True,
                                   env=dict(os.environ,
                                            **self.test_env)))
        return rvs

    def _run_test_command(self, command=[]):
        """
        Create a new test container, run a test command, collect the log output,
        evaluate the result, and return. Easy.
        Mimics the behavior of tools.run_command().
        :param command: The command to execute in the test container as list
        :return: same as tools.run_command()
        :raise: RunCommandError if the execution was not successful
        """
        dc = get_client()
        command_log = ["docker({})".format(self.test_image)]
        if len(command) > 0:
            command_log += command
        else:
            command_log.append("(default)")
        cid = create_container(self.test_image,
                               command=command, environment=self.test_env)
        self.cleanup_test_containers.append(cid)
        dc.start(container=cid,
                 links=[(self._container_for_service(service), service)
                        for service in self.test_linked_services])
        logs = dc.logs(cid,
                       stdout=True, stderr=True, stream=True,
                       follow=True, since=0)
        log_output = []
        for log in logs:
            log_output.append(str(log, encoding="UTF-8"))
        tmp = dc.inspect_container(cid)
        returncode = tmp['State']['ExitCode']
        rv = (command_log, returncode, "".join(log_output), None)
        if returncode != 0:
            ex = RunCommandError(
                command=command,
                stdout="\n".join(log_output),
                returncode=returncode
            )
            ex.rv = rv
            raise ex
        return rv

    def _setup_test_env(self):
        # make pulling standard.
        if self.meta.get('pull', True):
            self.compose_wrapper.pull(ignorefailures=True)
            # will not fail if the image is not pullable! :)
            get_client().pull(self.test_image)
        self.run_containers = self.compose_wrapper.up()

    def _cleanup(self):
        dc = get_client()
        self.compose_wrapper.kill()
        # this sucks. for older docker-compose versions, we need --all,
        # newer ones break with it.
        self.compose_wrapper.rm()
        for test_container_id in self.cleanup_test_containers:
            dc.remove_container(test_container_id)

    def _get_container_logs(self):
        pass

    def run(self):
        success = True
        try:
            self._setup_test_env()
            self._run_local_commands(self.meta.get('pre', None))
            if len(self.test_commands) > 0:
                for test_command in self.test_commands:
                    rv = self._run_test_command(test_command)
                    self.test_results.append(rv)
            else:
                # no explicit command given
                self.test_results.append(self._run_test_command())
            self._run_local_commands(self.meta.get('post', None))
            self.compose_wrapper.stop()
            self.compose_wrapper.rm()
        except KeyError as e:
            # raised by _container_for_service() if service cannot be found
            success = False
            self.reason = str(e)
        except RunCommandError as e:
            success = False
            self.reason = "Failed test command"
            self.test_results.append(e.rv)
        except OSError as e:
            success = False
            self.reason = "Exception while executing command: {}".format(str(e))
            self.log.error("Exception on command execution: {}".format(str(e)))
            self.test_results.append(e)
        finally:
            self._get_container_logs()
            self._cleanup()
        # evaluate test results
        if self.meta.get('allow_failure', False) and not success:
            self.test_state = self.CONTROLLED_FAILURE
        else:
            self.test_state = self.SUCCEEDED if success else self.FAILURE
        self.log.warning("test state %s" % self.test_state)
        return self.succeeded()

    def succeeded(self):
        return self.test_state in (self.SUCCEEDED, self.CONTROLLED_FAILURE)


if __name__ == "__main__":
    print("Don't do this :)")
