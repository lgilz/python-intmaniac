#!/usr/bin/env python

from intmaniac.testrun import Testrun
from tests.testmock import *
from tests.testconfigs import *

import unittest


class TestTestrun(unittest.TestCase):

    def setUp(self):
        self.testrun = Testrun('default', "/hoo/ha", **testrun_configs['default'])

    @unittest.skipUnless(mock_available,
                         "No mocking available in this Python version")
    @patch('intmaniac.testrun.run_command')
    def test_environment_setup(self, rc):
        wanted_service_tuples = [('default_one_1', 'one'), ('default_two_1', 'two')]
        wanted_command_base = ['docker', 'run', '--rm',
                               '-e', 'TARGET_URL=rsas',
                               '--link', 'default_two_1:two',
                               'my/testimage:latest']
        string_input = "creating default_one_1\ncreating default_two_1\n"
        rc.return_value = ("docker-compose", 0, None, string_input)
        tr = self.testrun
        # now test
        tr._setup_test_env()
        self.assertEqual(wanted_service_tuples, tr.run_containers)
        self.assertEqual(wanted_command_base, tr.run_command_base)

    def test_test_name_construction(self):
        tr = Testrun('default', "/hoo/ha", **testrun_configs['default'])
        self.assertEqual('default', tr.name)
        tr = Testrun(None, "/hoo/ha", **testrun_configs['default'])
        self.assertEqual('ha', tr.name)


if __name__ == "__main__":
    unittest.main()
