import intmaniac
from intmaniac import maniac_file
from tests.configsetup import *
from tests.mocksetup import *

import unittest


@unittest.skipUnless(mock_available, "No mocking available")
class TestV3File(unittest.TestCase):

    patch_pdct = 'intmaniac.maniac_file._prepare_docker_compose_template'

    def setUp(self):
        self.config = intmaniac._parse_args(["-e", "cmd=too"])

    def test_v3file_full(self):
        with patch(self.patch_pdct) as pdc:
            pdc.side_effect = lambda x, *args: x
            rv = maniac_file._parsev3(v3_config_0, self.config)
            self.assertEqual(9, len(rv))
            for tr in mock_testruns:
                self.assertTrue(tr in rv, "'{}' not in created tests"
                                .format(tr.name))

    def test_v3file_minimal(self):
        with patch(self.patch_pdct) as pdc:
            pdc.side_effect = lambda x, *args: x
            rv = maniac_file._parsev3(v3_config_minimal, self.config)
            self.assertEqual(1, len(rv))

    def test_v3_cmdline_propagation(self):
        with patch(self.patch_pdct) as pdc:
            pdc.side_effect = lambda x, *args: x
            rv = maniac_file._parsev3(v3_config_minimal, self.config)
            self.assertEqual(1, len(rv))
        self.assertTrue(pdc.call_count > 0)
        called = pdc.mock_calls[0][1][1]
        self.assertDictEqual({'cmd': 'too'}, called)
