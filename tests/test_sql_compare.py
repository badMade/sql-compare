import unittest
import sys
import os

# Add parent directory to path to import sql_compare
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sql_compare import canonicalize_select_list

class TestCanonicalizeSelectList(unittest.TestCase):

    def test_basic_reordering(self):
        sql = "SELECT b, a FROM t"
        expected = "SELECT a, b FROM t"
        self.assertEqual(canonicalize_select_list(sql), expected)

    def test_aliases(self):
        sql = "SELECT b AS y, a AS x FROM t"
        expected = "SELECT a AS x, b AS y FROM t"
        self.assertEqual(canonicalize_select_list(sql), expected)

    def test_functions(self):
        sql = "SELECT MIN(a), MAX(b) FROM t"
        expected = "SELECT MAX(b), MIN(a) FROM t"
        self.assertEqual(canonicalize_select_list(sql), expected)

    def test_complex_expressions(self):
        sql = "SELECT COALESCE(b, c), a FROM t"
        expected = "SELECT a, COALESCE(b, c) FROM t"
        self.assertEqual(canonicalize_select_list(sql), expected)

    def test_quoted_identifiers(self):
        sql = 'SELECT "b", "a" FROM t'
        expected = 'SELECT "a", "b" FROM t'
        self.assertEqual(canonicalize_select_list(sql), expected)

    def test_whitespace_collapsing(self):
        sql = "SELECT  b ,   a   FROM   t"
        expected = "SELECT a, b FROM t"
        self.assertEqual(canonicalize_select_list(sql), expected)

    def test_no_from_clause(self):
        sql = "SELECT 1, 2"
        expected = "SELECT 1, 2"
        self.assertEqual(canonicalize_select_list(sql), expected)

    def test_nested_functions_and_parens(self):
        sql = "SELECT COUNT(x), AVG(y) FROM t"
        expected = "SELECT AVG(y), COUNT(x) FROM t"
        self.assertEqual(canonicalize_select_list(sql), expected)

if __name__ == '__main__':
    unittest.main()
