#!/usr/bin/env pythpn

import unittest
from testrunner import prepare_environment, get_test_set_groups


class TestEmptyTemplate(unittest.TestCase):

    def setUp(self):
        prepare_environment("-c ../testdata/testconfig_empty.yaml".split())

    def testNumberOfTestsetsCreated(self):
        tsgs = get_test_set_groups()
        self.assertIsInstance(tsgs, list)
        self.assertEqual(len(tsgs), 1)
        self.assertIsInstance(tsgs[0], list)
        self.assertEqual(0, len(tsgs[0]))


class TestArrayTripleTest(unittest.TestCase):

    def setUp(self):
        prepare_environment("-c ../testdata/testconfig_array_triple.yaml".split())
        self.tsgs = get_test_set_groups()

    def test_number_of_tests_created(self):
        tsgs = self.tsgs
        self.assertIsInstance(tsgs, list)
        self.assertEqual(len(tsgs), 2)
        self.assertIsInstance(tsgs[0], list)
        self.assertIsInstance(tsgs[1], list)
        self.assertEqual(2, len(tsgs[0]))
        self.assertEqual(1, len(tsgs[1]))

    def test_given_names(self):
        tsgs = self.tsgs
        self.assertEqual(tsgs[0][0].name, "00-ts1")
        self.assertEqual(tsgs[0][1].name, "00-ts2")
        self.assertEqual(tsgs[1][0].name, "01-ts3")

    def test_environment_setting_and_propagation(self):
        tlcount = 0
        tscount = 1
        tcount = 1
        tsgs = self.tsgs
        for tlist in tsgs:
            for tset in tlist:
                tests = sorted(tset.tests, key=lambda x: x.name)
                for test in tests:
                    tname = "%02d-ts%d-test%d" % (tlcount, tscount, tcount)
                    self.assertEqual(tname, test.name)
                    self.assertEqual(test.test_env[str(tcount)], str(tcount))
                    tcount += 1
                tscount += 1
            tlcount += 1


if __name__ == "__main__":
    unittest.main()
