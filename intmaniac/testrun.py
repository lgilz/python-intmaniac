#!/usr/bin/env python

from intmaniac.tools import run_command, run_command_log as rcl
from intmaniac.tools import get_logger, RunCommandError
from intmaniac.dockhelpers import *

import os
from os.path import basename
from re import sub as resub, search as research, compile as recomp


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
        self.run_command_base = None
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

    def _run_docker_compose(self, command, *args, **kwargs):
        base_command = "docker-compose -f {} -p {}".format(
            self.template, self.sanitized_name
        ).split()
        use_command = command \
            if isinstance(command, list) \
            else command.split(" ")
        full_command = base_command + use_command
        rv = self._run_command(full_command, *args, **kwargs)
        return rv

    def _container_for_service(self, service_name):
        try:
            return next(filter(lambda x: x[1] == service_name,
                               self.run_containers))[0]
        except StopIteration as ex:
            # we cannot find the service name in the service list
            ex = KeyError("Cannot find service '{}' in started services"
                          .format(service_name))
            raise ex

    def _run_command(self, *args, **kwargs):
        """
        Convenience wrapper to actually always log command executions, even if
        they throw an error. Not really cool, but this way it's out of my mind.
        :param args: Arguments for run_command
        :param kwargs: Keyword arguments for run_command
        :return: The return tuple from run_command
        """
        try:
            rv = run_command(*args, **kwargs)
            rcl(self.log.error, self.log.debug, rv)
        except RunCommandError as e:
            rcl(self.log.error, self.log.debug, e.rv)
            raise e
        return rv

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
            rvs.append(self._run_command(command,
                                         throw=True,
                                         env=dict(os.environ,
                                                  **self.test_env)))
        return rvs

    def _run_test_command(self, command):
        """
        Create a new test container, run a test command, collect the log output,
        evaluate the result, and return. Easy.
        Mimics the behavior of tools.run_command().
        :param command: The command to execute in the test container
        :return: same as tools.run_command()
        :raise: RunCommandError if the execution was not successful
        """
        dc = get_client()
        cid = self._create_test_container_with_command(command)
        links = [(self._container_for_service(service), service)
                 for service in self.test_linked_services]
        dc.start(container=cid, links=links)
        logs = dc.logs(cid,
                       stdout=True, stderr=True, stream=True,
                       follow=True, since=0)
        log_output = []
        for log in logs:
            log_output.append(str(log, encoding="UTF-8"))
        tmp = dc.inspect_container(cid)
        returncode = tmp['State']['ExitCode']
        rv = (command, returncode, "".join(log_output), None)
        if returncode != 0:
            ex = RunCommandError(
                command=command,
                stdout="\n".join(log_output),
                returncode=returncode
            )
            ex.rv = rv
            raise ex
        return rv

    def _extract_container_names_from(self, outtext):
        matcher = recomp('({}_(.+)_[0-9]+)'.format(self.sanitized_name))
        lines = list(map(lambda x: x.strip(), outtext.split("\n")))
        lines = list(filter(lambda x: matcher.search(x) is not None, lines))
        run_containers = []
        for line in lines:
            match = matcher.search(line)
            run_containers.append((match.groups()[0], match.groups()[1]))
        self.run_containers = run_containers
        self.log.warning("FOUND TEST CONTAINERS: {}"
            .format(", ".join(
            ["{}->{}".format(k[0], k[1]) for k in self.run_containers]
        )))

    def _create_test_container_with_command(self, command=None):
        """
        Creates a new test container instance with the command given. Must be
        called for each command, because we can't change the command once
        it's set.
        :param command: The command to execute with the container
        :return: The container id string
        """
        dc = get_client()
        # the container is removed in self._cleanup()
        tmp = dc.create_container(self.test_image,
                                  environment=self.test_env,
                                  command=command)
        test_container_id = tmp['Id']
        self.cleanup_test_containers.append(test_container_id)
        return test_container_id

    def _setup_test_env(self):
        dc = get_client()
        if self.meta.get('pull', None):
            self._run_docker_compose("pull --ignore-pull-failures".split(),
                                     throw=True)
            dc.pull(self.test_image)
        rv = self._run_docker_compose("up -d", throw=True)
        # TODO - use docker api to extract container names
        # first, set up "container_name -> service_name" tuples
        outtext = rv[3]  # docker-compose outputs to stderr
        # TODO - replace self._container_for_service
        self._extract_container_names_from(rv[3])

    def _cleanup(self):
        dc = get_client()
        self._run_docker_compose("stop")
        # this sucks. for older docker-compose versions, we need --all,
        # newer ones break with it.
        self._run_docker_compose("rm -f")
        for test_container_id in self.cleanup_test_containers:
            dc.remove_container(test_container_id)

    def _get_container_logs(self):
        pass

    def run(self):
        success = True
        try:
            self._setup_test_env()
            self._run_local_commands(self.meta.get('pre', None))
            for test_command in self.test_commands:
                rv = self._run_test_command(test_command)
                self.test_results.append(rv)
            self._run_local_commands(self.meta.get('post', None))
            self._run_docker_compose("stop".split(" "))
            self._run_docker_compose("rm -f".split(" "))
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
            self.reason = "Exception while exeucting command: {}".format(str(e))
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
