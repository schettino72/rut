"""Manual test: colorized diff output.

Run with:
    rut manual_tests/test_diff_output.py

Expected: all tests FAIL with colorized diffs in panels.
  - red for '- ' lines (expected)
  - green for '+ ' lines (actual)
  - dim for '? ' pointer lines
"""
import unittest


class TestStringDiff(unittest.TestCase):

    def test_multiline_string(self):
        a = "line1\nline2\nline3\nline4\nline5"
        b = "line1\nline2\nLINE3_CHANGED\nline4\nline5"
        self.assertEqual(a, b)

    def test_single_line_string(self):
        self.assertEqual("hello world", "hello wrold")


class TestListDiff(unittest.TestCase):

    def test_list_one_element_changed(self):
        a = list(range(15))
        b = list(range(15))
        b[7] = 999
        self.assertEqual(a, b)

    def test_list_different_length(self):
        self.assertEqual([1, 2, 3], [1, 2, 3, 4, 5])


class TestDictDiff(unittest.TestCase):

    def test_dict_value_changed(self):
        a = {"name": "alice", "age": 30, "city": "paris"}
        b = {"name": "alice", "age": 31, "city": "london"}
        self.assertEqual(a, b)

    def test_dict_key_missing(self):
        a = {"x": 1, "y": 2, "z": 3}
        b = {"x": 1, "z": 3}
        self.assertEqual(a, b)
