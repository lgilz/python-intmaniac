#!/usr/bin/env python

from intmaniac import _prepare_environment, _get_test_sets
from intmaniac import _get_and_init_configuration
from intmaniac.testrun import Testrun
from intmaniac.tools import enable_debug, _construct_return_object

import unittest
import os

# this is python3 testing only.
# so let's make sure this is not executed on python2
# that sucks *so* much.
mock_available = False
try:
    # python 3.something
    from unittest.mock import patch
    from unittest.mock import call
    mock_available = True
except ImportError:
    try:
        # python < 3.something with mock installed
        from mock import patch, call
        mock_available = True
    except ImportError:
        pass
# did I mention this sucks?


class TestSimpleExecution(unittest.TestCase):

    def construct_base_cmdline(self, test_name):
        """returns (test_basedir, test_dir, base_cmd_line)"""
        test_basedir = "/tmp/intmaniac_00001"
        test_dir = os.path.join(test_basedir, test_name)
        base_cmdline = [
            'docker-compose', 'run', '-e',
            "test_dir=%s" % test_dir,
            '--rm', 'test-service']
        return test_basedir, test_dir, base_cmdline

    def setUp(self):
        enable_debug()
        self.test_basedir, self.test_dir, self.base_cmdline = \
            self.construct_base_cmdline("real-test0")
        pass

    @unittest.skipUnless(mock_available, "No mocking available in this Python version")
    def test_simple_string_execution(self):
        _prepare_environment("-c testdata/command_exec_test.yaml -vvvvv".split())
        config = _get_and_init_configuration()
        testsets = _get_test_sets(config)
        with patch("intmaniac.testrun.run_command") as mock:
            mock.side_effect = [
                # args, returncode, stdout is the constructor.
                _construct_return_object(0, [], "ho1"),
                _construct_return_object(0, [], "hi"),
                _construct_return_object(0, [], "ho2"),
                _construct_return_object(0, [], None),
                _construct_return_object(0, [], None),
            ]
            expected_calls = [
                call(self.base_cmdline+"sleep 1".split(), cwd=self.test_dir),
                call(self.base_cmdline+"echo hi".split(), cwd=self.test_dir),
                call(self.base_cmdline+"sleep 2".split(), cwd=self.test_dir),
                call("docker-compose kill".split(" "), cwd=self.test_dir),
                call("docker-compose rm -f".split(" "), cwd=self.test_dir),
            ]
            result = testsets[0].tests[0].run()
            # if you step through here with the IDE the results will be
            # fucked. cause the IDE interferes with the mock.
            # just so you remember.
            self.assertEqual(5, len(mock.mock_calls))
            for want, act in zip(expected_calls, mock.mock_calls):
                self.assertEqual(want, act,
                                 msg="WANT: \n{}IS:   \n{}\n".format(str(want), str(act)))
        for test in testsets[0].tests:
            self.assertIsNone(test.exception)
        self.assertTrue(result)

    @unittest.skipUnless(mock_available, "No mocking available in this Python version")
    def test_execute_command_lists(self):
        _prepare_environment("-c testdata/command_exec_test.yaml -vvvvv".split())
        config = _get_and_init_configuration()
        testsets = _get_test_sets(config)
        for test_num, test in enumerate(testsets[0].tests[1:], start=1):
            with patch("intmaniac.testrun.run_command") as mock:
                _, test_dir, base_cmdline = \
                    self.construct_base_cmdline("real-test%d"%test_num)
                mock.side_effect = [
                    # args, returncode, stdout is the constructor.
                    _construct_return_object(0, [], "ho1"),
                    _construct_return_object(0, [], "ho2"),
                    _construct_return_object(0, [], "hi"),
                    _construct_return_object(0, [], "ho"),
                    _construct_return_object(0, [], "ho3"),
                    _construct_return_object(0, [], "ho4"),
                    _construct_return_object(0, [], None),
                    _construct_return_object(0, [], None),
                ]
                expected_calls = [
                    call(base_cmdline+"sleep 1".split(), cwd=test_dir),
                    call(base_cmdline+"sleep 2".split(), cwd=test_dir),
                    call(base_cmdline+"echo hi".split(), cwd=test_dir),
                    call(base_cmdline+"echo ho".split(), cwd=test_dir),
                    call(base_cmdline+"sleep 3".split(), cwd=test_dir),
                    call(base_cmdline+"sleep 4".split(), cwd=test_dir),
                    call("docker-compose kill".split(" "), cwd=test_dir),
                    call("docker-compose rm -f".split(" "), cwd=test_dir),
                ]
                result = test.run()
                self.assertIsNone(test.exception)
                self.assertTrue(result)
                # if you step through here with the IDE the results will be
                # fucked. cause the IDE interferes with the mock.
                # just so you remember.
                self.assertEqual(len(expected_calls), len(mock.mock_calls))
                for want, act in zip(expected_calls, mock.mock_calls):
                    self.assertEqual(want, act,
                                     msg="\nWANT: {}\nIS:   {}\n".format(str(want), str(act)))

    @unittest.skipUnless(mock_available,
                         "No mocking available in this Python version")
    def test_for_allowed_failure(self):
        _, test_dir, base_cmdline = self.construct_base_cmdline("real-test0")
        _prepare_environment("-c testdata/command_exec_test.yaml -vvvvv".split())
        config = _get_and_init_configuration()
        testsets = _get_test_sets(config)
        tst = testsets[0].tests[0]
        # we inject the allow_failure attribute here.
        tst.test_meta['allow_failure'] = True
        with patch("intmaniac.testrun.run_command") as mock:
            mock.side_effect = [
                _construct_return_object(1, ['oioi'], "error simulation"),
                _construct_return_object(0, [], None),
                _construct_return_object(0, [], None),
            ]
            expected_calls = [
                # fails on the before_test command, so ....
                call(base_cmdline+"sleep 1".split(), cwd=test_dir),
                # ... the next command is the cleanup.
                call("docker-compose kill".split(" "), cwd=test_dir),
                call("docker-compose rm -f".split(" "), cwd=test_dir),
            ]
            result = tst.run()
        self.assertTrue(result)
        self.assertEqual(Testrun.CONTROLLED_FAILURE, tst.state)
        for want, act in zip(expected_calls, mock.mock_calls):
            self.assertEqual(want, act,
                             msg="\nWANT: {}\nIS:   {}\n"
                             .format(str(want), str(act)))
