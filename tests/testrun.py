#!/usr/bin/env python

import intmaniac
from intmaniac.tools import RunCommandError
from tests.mocksetup import *
from tests.configsetup import get_test_tr
from tests.fake_container import FakeContainer

import tests.configsetup

import unittest


class TestTestrun(unittest.TestCase):

    def test_test_name_construction(self):
        tr_obj = get_test_tr('default')
        self.assertEqual('default', tr_obj.name)
        tr_obj = get_test_tr('default', name=None)
        self.assertEqual('ha', tr_obj.name)

    @unittest.skipUnless(mock_available, "No mocking available")
    def test_testcommand_execution(self):
        tr_obj = get_test_tr('nocommands')
        tmp0 = MagicMock()
        tmp1 = ("sim_command", 0, "out", "err")
        tr_obj.compose_wrapper = tmp0
        tmp0.up.return_value = [("asdf_two_1", "two"), ]
        tmp0.kill.return_value = tmp1
        tmp0.stop.return_value = tmp1
        tmp0.rm.return_value = tmp1
        with patch('tests.configsetup.tr.run_command') as mock_rc, \
            patch('tests.configsetup.tr.create_container') as mock_cc, \
            patch('tests.configsetup.tr.get_client') as mock_gc:
            # what will happen is:
            #    dc = get_client() called
            #    create_container() called, should return a docker.container-obj
            #    dc.start(...), dc.logs(...) called, return value not so
            #        important
            #    dc.inspect_container called, should return dict with
            #        rv['State']['ExitCode'] present
            # done.
            mock_cc.return_value = FakeContainer(
                id='0815',
                attrs=dict(State=dict(ExitCode=0))
            )
            mock_rc.side_effect = [
                ("sleep 10", 0, ":)", "None"),
            ]
            tr_obj.run()
            self.assertTrue(tr_obj.succeeded())
            # check execution counts
            self.assertEqual(1, mock_rc.call_count)    # for 'sleep 10'
            self.assertEqual(1, mock_cc.call_count)    # for the one test run
            self.assertEqual(3, mock_gc.call_count)    # pull, test run, cleanup
            # check the execution content
            self.assertEqual(['sleep', '10'], mock_rc.call_args[0][0])
            self.assertEqual(call('my/testimage:latest',
                                  command=[],
                                  environment={'TARGET_URL': 'rsas'},
                                  links=[('asdf_two_1', 'two')],
                                  volumes={}),
                             mock_cc.call_args)

    @unittest.skipUnless(mock_available, "No mocking available")
    def test_exception_handling(self):
        # set up base objects
        argconfig0 = intmaniac._parse_args("-e my_image=my/image".split())
        argconfig1 = intmaniac._parse_args("-e my_image=my/image "
                                           "--no-format-output".split())
        tr_obj = get_test_tr('nocommands')
        # configure test env
        tmp0 = MagicMock()
        tmp1 = ("sim_command", 0, "out", "err")
        tr_obj.compose_wrapper = tmp0
        tmp0.up.return_value = [("asdf_two_1", "two"), ]
        tmp0.kill.return_value = tmp1
        tmp0.stop.return_value = tmp1
        tmp0.rm.return_value = tmp1
        for argconfig in (argconfig0, argconfig1):
            for side_effect in (
                RunCommandError(returncode=1, stdout="RCError test",
                                command=["totally false"]),
                KeyError("KeyError test"), OSError("OSerror test"),
            ):
                with patch('tests.configsetup.tr.run_command') as mock_rc, \
                        patch('tests.configsetup.tr.create_container') as mock_cc, \
                        patch('tests.configsetup.tr.get_client') as mock_gc:
                    mock_cc.return_value = '0815'
                    mock_gc.return_value.inspect_container.return_value = {
                        'State': {'ExitCode': 0}
                    }
                    mock_rc.side_effect = side_effect
                    intmaniac._run_tests(argconfig, [tr_obj])
                    self.assertFalse(tr_obj.succeeded())


if __name__ == "__main__":
    unittest.main()
