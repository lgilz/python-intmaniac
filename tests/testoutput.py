import intmaniac
from intmaniac import output
from intmaniac.output.teamcity import TeamcityOutput
from intmaniac.output.base import GenericOutput
from tests.mocksetup import *
from tests.configsetup import *

import unittest


class TestOutput(unittest.TestCase):

    def test_init_output_exception(self):
        with self.assertRaises(ImportError):
            output.init_output("blah")

    def test_init_output_function(self):
        output.init_output("teamcity")
        self.assertIsInstance(output.output, TeamcityOutput)

    @unittest.skipUnless(mock_available, "No mocking available")
    def test_output_initialization(self):
        with patch('intmaniac.maniac_file.parse') as mock_parse:
            mock_parse.return_value = []
            intmaniac._internal_entrypoint([])
        self.assertIsInstance(output.output, GenericOutput)
        with patch('intmaniac.maniac_file.parse') as mock_parse:
            mock_parse.return_value = []
            intmaniac._internal_entrypoint("-o teamcity".split())
        self.assertIsInstance(output.output, TeamcityOutput)

    @unittest.skipUnless(mock_available, "No mocking available")
    def test_teamcity_output(self):
        """
        Only tests if the output methods don't throw an exception.
        :return: None
        """
        # we need this otherwise we will get a "test error" with unit tests.
        # don't know why.
        with patch.object(TeamcityOutput, 'dump'):
            op = TeamcityOutput()
            op.message("meh")
            op.message("meh", "mah")
            op.message("meh", "mah", "muh")
            op.block_open("block")
            op.test_suite_open("suite")
            op.test_open("test")
            op.test_stderr("whoops")
            op.test_stdout("okay")
            op.test_failed("meh")
            op.test_failed("meh", "mehmah")
            op.test_failed("meh", "mehmeh", "mehmah")
            op.test_done()
            op.test_suite_done()
            op.block_done()

    @unittest.skipUnless(mock_available, "No mocking available")
    def test_text_output(self):
        """
        Only tests if the output methods don't throw an exception.
        :return: None
        """
        # we need this otherwise we will get a "test error" with unit tests.
        # don't know why.
        with patch.object(GenericOutput, 'dump'):
            op = GenericOutput()
            op.message("meh")
            op.message("meh", "mah")
            op.message("meh", "mah", "muh")

            op.block_open("block")
            op.block_done()

            op.test_suite_open("suite")
            op.test_open("test")
            op.test_stderr("whoops")
            op.test_stdout("okay")
            op.test_failed("meh")
            op.test_failed("meh", "mehmah")
            op.test_failed("meh", "mehmeh", "mehmah")
            op.test_done()
            op.test_suite_done()

            op.test_open("test")
            op.test_done(2)

            op.test_open("test")
            op.test_done(2.5)

