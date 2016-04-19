import intmaniac
from intmaniac import maniac_file
from tests.testconfigs import *
from tests.testmock import *

import unittest


@unittest.skipUnless(mock_available, "No mocking available")
class TestV3File(unittest.TestCase):

    def setUp(self):
        with patch('intmaniac.isfile') as isf:
            isf.return_value = True
            self.config = intmaniac._parse_args([])

    def test_v3fileformat(self):
        with patch('intmaniac.maniac_file._prepare_docker_compose_template') as pdc:
            pdc.side_effect = lambda x, *args: x
            rv = maniac_file._parsev3(v3_config_0, self.config)
            self.assertEqual(9, len(rv))
            for tr in mock_testruns:
                self.assertTrue(tr in rv, "'{}' not in created tests"
                                .format(tr.name))

