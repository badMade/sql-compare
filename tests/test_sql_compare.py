import unittest
import sys
import os

# Add parent directory to path so we can import sql_compare.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sql_compare

class TestParseFromClauseBody(unittest.TestCase):
    def test_basic_inner_join(self):
        body = "t1 JOIN t2 ON t1.id = t2.id"
        base, segments = sql_compare._parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["type"], "INNER")
        self.assertEqual(segments[0]["table"], "t2")
        self.assertEqual(segments[0]["cond_kw"], "ON")
        self.assertEqual(segments[0]["cond"], "t1.id = t2.id")

    def test_explicit_inner_join(self):
        body = "t1 INNER JOIN t2 ON t1.id = t2.id"
        base, segments = sql_compare._parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["type"], "INNER")

    def test_left_join(self):
        body = "t1 LEFT JOIN t2 ON t1.id = t2.id"
        base, segments = sql_compare._parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["type"], "LEFT")

    def test_multiple_joins(self):
        body = "t1 JOIN t2 ON t1.id = t2.id LEFT JOIN t3 ON t2.id = t3.id"
        base, segments = sql_compare._parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0]["type"], "INNER")
        self.assertEqual(segments[1]["type"], "LEFT")
        self.assertEqual(segments[1]["table"], "t3")

    def test_implicit_cross_join(self):
        body = "t1, t2"
        base, segments = sql_compare._parse_from_clause_body(body)
        self.assertEqual(base, "t1, t2")
        self.assertEqual(len(segments), 0)

    def test_cross_join_keyword(self):
        body = "t1 CROSS JOIN t2"
        base, segments = sql_compare._parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["type"], "CROSS")
        self.assertIsNone(segments[0]["cond_kw"])

    def test_nested_parentheses_ignored(self):
        # Joins inside parentheses (subqueries) should not be split
        body = "t1 JOIN (SELECT * FROM t2 JOIN t3 ON t2.id=t3.id) sub ON t1.id = sub.id"
        base, segments = sql_compare._parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["type"], "INNER")
        self.assertTrue(segments[0]["table"].startswith("(SELECT"))
        self.assertIn("JOIN t3", segments[0]["table"])

    def test_quoted_keywords_ignored(self):
        body = "t1 JOIN t2 ON t1.col = 'LEFT JOIN'"
        base, segments = sql_compare._parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["type"], "INNER")
        self.assertEqual(segments[0]["cond"], "t1.col = 'LEFT JOIN'")

    def test_mixed_case_whitespace(self):
        body = "  t1   Left   OUTER   JOIN   t2   ON   t1.id = t2.id  "
        base, segments = sql_compare._parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["type"], "LEFT")
        self.assertEqual(segments[0]["table"], "t2")

if __name__ == '__main__':
    unittest.main()
