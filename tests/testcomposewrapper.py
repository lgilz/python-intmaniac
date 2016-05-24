from tests.mocksetup import *
from intmaniac import dockhelpers

import unittest


class TestComposeWrapper(unittest.TestCase):

    @unittest.skipUnless(mock_available, "No mocking available")
    @patch('intmaniac.dockhelpers.tools.run_command')
    def test_up_container_name_extraction(self, rc):
        wanted_test_base = 'waha'
        cm_obj = dockhelpers.Compose(template="/wah/wo",
                                     project_name=wanted_test_base)
        wanted_service_tuples = [('{}_one_1'.format(wanted_test_base), 'one'),
                                 ('{}_two_1'.format(wanted_test_base), 'two'),
                                 ('{}_thr_1'.format(wanted_test_base), 'thr'),
                                 ('{}_for_1'.format(wanted_test_base), 'for')]
        simulated_dc_output = "creating {0}_one_1\n" \
                              "shoo shabala\n" \
                              "creating {0}_two_1\n"\
                              "creating {0}_thr_1...\n"\
                              "creating {0}_for_1 ...\n"\
                              .format(wanted_test_base)
        rc.return_value = ("docker-compose", 0, None, simulated_dc_output)
        # now test
        rv = cm_obj.up()
        self.assertEqual(wanted_service_tuples, rv)
