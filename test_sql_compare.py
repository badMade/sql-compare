import unittest
import re
from sql_compare import (
    uppercase_outside_quotes,
    remove_outer_parentheses,
    split_top_level,
    top_level_find_kw,
    _parse_from_clause_body,
    _rebuild_from_body
)

class TestSQLRefactor(unittest.TestCase):
    def test_uppercase_outside_quotes(self):
        # Basic
        self.assertEqual(uppercase_outside_quotes("select * from t"), "SELECT * FROM T")
        # Quotes
        self.assertEqual(uppercase_outside_quotes("select 'a' from t"), "SELECT 'a' FROM T")
        self.assertEqual(uppercase_outside_quotes('select "a" from t'), 'SELECT "a" FROM T')
        # Escaped quotes (SQL standard uses double single quotes)
        self.assertEqual(uppercase_outside_quotes("select 'it''s' from t"), "SELECT 'it''s' FROM T")
        # Brackets and backticks
        self.assertEqual(uppercase_outside_quotes("select [MyCol] from `MyTable`"), "SELECT [MyCol] FROM `MyTable`")
        # Mixed
        self.assertEqual(uppercase_outside_quotes("select 'a', \"b\", [c], `d`"), "SELECT 'a', \"b\", [c], `d`")
        # Parentheses (should be uppercased as they are not quotes)
        self.assertEqual(uppercase_outside_quotes("select count(x)"), "SELECT COUNT(X)")

    def test_remove_outer_parentheses(self):
        self.assertEqual(remove_outer_parentheses("(select 1)"), "select 1")
        self.assertEqual(remove_outer_parentheses("((select 1))"), "select 1")
        self.assertEqual(remove_outer_parentheses("(select 1) union (select 2)"), "(select 1) union (select 2)")
        self.assertEqual(remove_outer_parentheses("(select ')' from t)"), "select ')' from t")
        self.assertEqual(remove_outer_parentheses("(select '(')"), "select '('")
        # Edge case: unbalanced parens or complex nesting handled gracefully
        self.assertEqual(remove_outer_parentheses("(a) b"), "(a) b")

    def test_split_top_level(self):
        self.assertEqual(split_top_level("a, b, c", ","), ["a", "b", "c"])
        self.assertEqual(split_top_level("a, 'b,c', d", ","), ["a", "'b,c'", "d"])
        self.assertEqual(split_top_level("func(a, b), c", ","), ["func(a, b)", "c"])
        self.assertEqual(split_top_level("case when a then b else c end, d", ","), ["case when a then b else c end", "d"])

    def test_top_level_find_kw(self):
        # Basic (Expects uppercase or matching case)
        self.assertEqual(top_level_find_kw("SELECT * FROM T", "FROM"), 9)
        # Inside quotes (should not find)
        self.assertEqual(top_level_find_kw("SELECT 'FROM' FROM T", "FROM"), 14)
        # Inside parens
        self.assertEqual(top_level_find_kw("SELECT (SELECT 1 FROM X) FROM T", "FROM"), 25)

    def test_parse_from_clause_body(self):
        # Basic
        base, segs = _parse_from_clause_body("t1 INNER JOIN t2 ON t1.id = t2.id")
        self.assertEqual(base, "t1")
        self.assertEqual(len(segs), 1)
        self.assertEqual(segs[0]['type'], 'INNER')
        self.assertEqual(segs[0]['table'], 't2')
        self.assertEqual(segs[0]['cond_kw'], 'ON')

        # Complex with parens and quotes
        body = "t1 LEFT JOIN (SELECT * FROM t2) AS sub ON sub.id = t1.id"
        base, segs = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segs), 1)
        self.assertEqual(segs[0]['type'], 'LEFT')
        self.assertEqual(segs[0]['table'], "(SELECT * FROM t2) AS sub")

if __name__ == '__main__':
    unittest.main()
