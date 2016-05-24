#!/usr/bin/env python

from tests.mocksetup import *
from tests.configsetup import get_test_tr

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
        with patch('configsetup.tr.run_command') as mock_rc, \
            patch('configsetup.tr.create_container') as mock_cc, \
            patch('configsetup.tr.get_client') as mock_gc:
            # what will happen is:
            #    dc = get_client() called
            #    create_container() called, should return an ID string
            #    dc.start(...), dc.logs(...) called, return value not so
            #        important
            #    dc.inspect_container called, should return dict with
            #        rv['State']['ExitCode'] present
            # done.
            mock_cc.return_value = '0815'
            mock_rc.side_effect = [
                ("sleep 10", 0, ":)", "None"),
            ]
            mock_gc.return_value.inspect_container.return_value = {
                'State': {'ExitCode': 0}
            }
            tr_obj.run()
            self.assertTrue(tr_obj.succeeded())
            # check execution counts
            self.assertEqual(1, mock_rc.call_count)    # for 'sleep 10'
            self.assertEqual(1, mock_cc.call_count)    # for the one test run
            self.assertEqual(3, mock_gc.call_count)    # pull, test run, cleanup
            self.assertEqual(1, mock_gc.return_value.pull.call_count)
            # check the execution content
            self.assertEqual(['sleep', '10'], mock_rc.call_args[0][0])
            self.assertEqual(call('my/testimage:latest',
                                  command=[],
                                  environment={'TARGET_URL': 'rsas'}),
                             mock_cc.call_args)



if __name__ == "__main__":
    unittest.main()
