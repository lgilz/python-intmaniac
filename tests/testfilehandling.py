import intmaniac
from intmaniac import maniac_file
from tests.configsetup import *
from tests.mocksetup import *

import yaml

from unittest import TestCase, skipUnless


class TestIntmaniacFileHandling(TestCase):

    def setUp(self):
        self.config_empty = intmaniac._parse_args([])
        self.config_env = intmaniac._parse_args(["-e", "my_image=my/image"])

    @patch('intmaniac.maniac_file._parsev2')
    @patch('intmaniac.maniac_file._parsev3')
    @patch('intmaniac.maniac_file.isfile')
    @patch('intmaniac.maniac_file.open')
    @skipUnless(mock_available, "No mocking available")
    def testIntmaniacReading(self, m_open, m_isfile, *_):
        m_open.return_value.__enter__.return_value.read.return_value = \
            v3_config_minimal_str
        m_isfile.return_value = 21
        maniac_file.parse(self.config_empty)

    @patch('intmaniac.maniac_file._parsev2')
    @patch('intmaniac.maniac_file._parsev3')
    @patch('intmaniac.maniac_file.isfile')
    @patch('intmaniac.maniac_file.open')
    @skipUnless(mock_available, "No mocking available")
    def testFailureOnMissingReplacement(self, m_open, m_isfile, *_):
        m_open.return_value.__enter__.return_value.read.return_value = \
            v3_config_rep_str
        m_isfile.return_value = 21
        with self.assertRaises(SystemExit):
            maniac_file.parse(self.config_empty)

    @patch('intmaniac.maniac_file._parsev2')
    @patch('intmaniac.maniac_file._parsev3')
    @patch('intmaniac.maniac_file.isfile')
    @patch('intmaniac.maniac_file.open')
    @skipUnless(mock_available, "No mocking available")
    def testGlobalReplacement(self, m_open, m_isfile, *_):
        m_open.return_value.__enter__.return_value.read.return_value = \
            v3_config_rep_str
        m_isfile.return_value = 21
        maniac_file.parse(self.config_env)
