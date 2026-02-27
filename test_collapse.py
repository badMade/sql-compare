import unittest
from sql_compare import collapse_whitespace

class TestCollapseWhitespace(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(collapse_whitespace("  SELECT   *  FROM  t  "), "SELECT * FROM t")

    def test_newlines_tabs(self):
        self.assertEqual(collapse_whitespace("SELECT\n\t* FROM\n\tt"), "SELECT * FROM t")

    def test_empty(self):
        self.assertEqual(collapse_whitespace("   "), "")
        self.assertEqual(collapse_whitespace(""), "")

    def test_no_change(self):
        self.assertEqual(collapse_whitespace("SELECT * FROM t"), "SELECT * FROM t")

if __name__ == '__main__':
    unittest.main()
