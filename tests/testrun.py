#!/usr/bin/env python

from intmaniac.testrun import Testrun
from tests.mocksetup import *
from tests.configsetup import *

import unittest


class TestTestrun(unittest.TestCase):

    def setUp(self):
        self.testrun = Testrun('default', "/hoo/ha", **testrun_configs['default'])

    @unittest.skipUnless(mock_available,
                         "No mocking available in this Python version")
    @patch('intmaniac.testrun.run_command')
    def test_environment_setup(self, rc):
        wanted_test_base = 'defaultha'
        wanted_service_tuples = [('{}_one_1'.format(wanted_test_base), 'one'),
                                 ('{}_two_1'.format(wanted_test_base), 'two')]
        wanted_command_base = ['docker', 'run', '--rm',
                               '-e', 'TARGET_URL=rsas',
                               '--link', 'defaultha_two_1:two',
                               'my/testimage:latest']
        simulated_dc_output = "creating {0}_one_1\n" \
                              "shoo shabala\n" \
                              "creating {0}_two_1\n".format(wanted_test_base)
        rc.return_value = ("docker-compose", 0, None, simulated_dc_output)
        tr = self.testrun
        # now test
        tr._setup_test_env()
        self.assertEqual(wanted_service_tuples, tr.run_containers)
        self.assertEqual(wanted_command_base, tr.run_command_base)

    def test_test_name_construction(self):
        tr = Testrun('default', "/hoo/ha", **testrun_configs['default'])
        self.assertEqual('default-ha', tr.name)
        tr = Testrun(None, "/hoo/ha", **testrun_configs['default'])
        self.assertEqual('ha', tr.name)


if __name__ == "__main__":
    unittest.main()
