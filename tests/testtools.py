import unittest

from intmaniac.tools import deep_merge, recursive_replace


class TestDeepMerge(unittest.TestCase):

    def test_basic_function(self):
        d0 = {1: 2}
        d1 = {2: 3}
        result = {1: 2, 2: 3}
        self.assertDictEqual(deep_merge(d0, d1), result)

    def test_key_priority(self):
        d0 = {1: 2, 2: [1, 2, 3]}
        d1 = {1: 3, 2: 3}
        result = {1: 3, 2: 3}
        self.assertDictEqual(deep_merge(d0, d1), result)

    def test_deep_merging(self):
        d0 = {1: {2: 3, 3: 4}, 7: 8}
        d1 = {1: {4: 5, 3: 3}, 8: 9}
        result = {1: {2: 3, 3: 3, 4: 5}, 7: 8, 8: 9}
        self.assertDictEqual(deep_merge(d0, d1), result)

    def test_more_than_two_arguments(self):
        d0 = {1: 2, 2: 3, 3: 4            }
        d1 = {      2: 4, 3: 5, 4: 6      }
        d2 = {            3: 6,       5: 8}
        rs = {1: 2, 2: 4, 3: 6, 4: 6, 5: 8}
        self.assertDictEqual(rs, deep_merge(d0, d1, d2))


class TestRecursiveReplace(unittest.TestCase):

    def test_recursive_replace(self):
        t0 = {'hey': 'ho', 'ha': {'hi': 'huho'}, 'k': ['heh', 'hoh', 'han']}
        t1 = {'hey': 'HI', 'ha': {'hi': 'huHI'}, 'k': ['heh', 'HIh', 'han']}
        res = recursive_replace(t0, "ho", "HI")
        self.assertDictEqual(t1, res)
