import unittest
import re
from sql_compare import (
    split_top_level,
    uppercase_outside_quotes,
    remove_outer_parentheses,
    top_level_find_kw,
    _parse_from_clause_body,
    _rebuild_from_body
)

class TestRefactor(unittest.TestCase):
    def test_split_top_level(self):
        s = "a, b, 'c,d', (e,f)"
        parts = split_top_level(s, ",")
        self.assertEqual(parts, ["a", "b", "'c,d'", "(e,f)"])

        self.assertEqual(split_top_level("a,b", ","), ["a", "b"])
        self.assertEqual(split_top_level("a, 'b,c'", ","), ["a", "'b,c'"])
        self.assertEqual(split_top_level("func(a,b), c", ","), ["func(a,b)", "c"])

    def test_uppercase_outside_quotes(self):
        s = "select 'abc' as x, \"def\" as y from [table]"
        expected = "SELECT 'abc' AS X, \"def\" AS Y FROM [table]"
        self.assertEqual(uppercase_outside_quotes(s), expected)

    def test_remove_outer_parentheses(self):
        self.assertEqual(remove_outer_parentheses("(select 1)"), "select 1")
        self.assertEqual(remove_outer_parentheses("((select 1))"), "select 1")
        self.assertEqual(remove_outer_parentheses("(a) union (b)"), "(a) union (b)")
        self.assertEqual(remove_outer_parentheses("(')')"), "')'")

    def test_top_level_find_kw(self):
        s = "SELECT * FROM t WHERE a='where'"
        self.assertEqual(top_level_find_kw(s, "WHERE"), 16)
        self.assertEqual(top_level_find_kw(s, "FROM"), 9)
        self.assertEqual(top_level_find_kw("'SELECT'", "SELECT"), -1)
        self.assertEqual(top_level_find_kw("myselect", "select"), -1)
        self.assertEqual(top_level_find_kw("selectx", "select"), -1)
        self.assertEqual(top_level_find_kw(" select ", "select"), 1)

    def test_parse_from_clause_body(self):
        body = "t1 INNER JOIN t2 ON t1.id = t2.id LEFT JOIN t3 ON t2.id = t3.id"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0]['type'], 'INNER')
        self.assertEqual(segments[0]['table'], 't2')
        self.assertEqual(segments[1]['type'], 'LEFT')
        self.assertEqual(segments[1]['table'], 't3')

    def test_parse_from_clause_body_bug_reproduction(self):
        body = "t1 JOIN t2 ON t1.id = t2.id"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(segments[0]['type'], 'INNER')
        rebuilt = _rebuild_from_body(base, segments)
        self.assertNotIn("JOIN JOIN", rebuilt)
        self.assertIn("t1 JOIN t2", rebuilt)

if __name__ == '__main__':
    unittest.main()
