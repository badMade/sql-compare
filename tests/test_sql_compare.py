import unittest
import sys
import os

# Add parent directory to path to import sql_compare
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sql_compare import _parse_from_clause_body

class TestParseFromClauseBody(unittest.TestCase):

    def test_simple_inner_join(self):
        body = "t1 JOIN t2 ON t1.id = t2.id"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["type"], "INNER")
        self.assertEqual(segments[0]["table"], "t2")
        self.assertEqual(segments[0]["cond_kw"], "ON")
        self.assertEqual(segments[0]["cond"], "t1.id = t2.id")

    def test_explicit_inner_join(self):
        body = "t1 INNER JOIN t2 ON t1.id = t2.id"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["type"], "INNER")
        self.assertEqual(segments[0]["table"], "t2")

    def test_left_join(self):
        body = "t1 LEFT JOIN t2 ON t1.id = t2.id"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["type"], "LEFT")
        self.assertEqual(segments[0]["table"], "t2")

    def test_left_outer_join(self):
        body = "t1 LEFT OUTER JOIN t2 ON t1.id = t2.id"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["type"], "LEFT") # OUTER is stripped
        self.assertEqual(segments[0]["table"], "t2")

    def test_right_join(self):
        body = "t1 RIGHT JOIN t2 ON t1.id = t2.id"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["type"], "RIGHT")
        self.assertEqual(segments[0]["table"], "t2")

    def test_full_join(self):
        body = "t1 FULL JOIN t2 ON t1.id = t2.id"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["type"], "FULL")
        self.assertEqual(segments[0]["table"], "t2")

    def test_cross_join(self):
        body = "t1 CROSS JOIN t2"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["type"], "CROSS")
        self.assertEqual(segments[0]["table"], "t2")
        self.assertEqual(segments[0]["cond"], "")

    def test_natural_join(self):
        body = "t1 NATURAL JOIN t2"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["type"], "NATURAL")
        self.assertEqual(segments[0]["table"], "t2")

    def test_natural_left_join(self):
        body = "t1 NATURAL LEFT JOIN t2"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["type"], "NATURAL LEFT")
        self.assertEqual(segments[0]["table"], "t2")

    def test_using_clause(self):
        body = "t1 JOIN t2 USING (id)"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(segments[0]["cond_kw"], "USING")
        self.assertEqual(segments[0]["cond"], "(id)")

    def test_multiple_joins(self):
        body = "t1 JOIN t2 ON t1.id = t2.id LEFT JOIN t3 ON t2.id = t3.id"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 2)
        # The implementation returns 'JOIN' for a simple JOIN, not 'INNER'
        self.assertEqual(segments[0]["type"], "JOIN")
        self.assertEqual(segments[0]["table"], "t2")
        self.assertEqual(segments[1]["type"], "LEFT")
        self.assertEqual(segments[1]["table"], "t3")
        self.assertEqual(segments[1]["cond"], "t2.id = t3.id")

    def test_subquery_table(self):
        body = "t1 JOIN (SELECT * FROM t2) s ON t1.id = s.id"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(segments[0]["table"], "(SELECT * FROM t2) s")
        self.assertEqual(segments[0]["cond"], "t1.id = s.id")

    def test_complex_condition(self):
        body = "t1 JOIN t2 ON t1.id = t2.id AND (t1.x = 1 OR t2.y = 2)"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(segments[0]["cond"], "t1.id = t2.id AND (t1.x = 1 OR t2.y = 2)")

    def test_mixed_case(self):
        body = "t1 Left Join t2 on t1.id = t2.id"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(segments[0]["type"], "LEFT")
        self.assertEqual(segments[0]["cond_kw"], "ON")

    def test_whitespace_handling(self):
        body = "  t1   JOIN    t2   ON   t1.id   =   t2.id  "
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(segments[0]["table"], "t2")
        self.assertEqual(segments[0]["cond"], "t1.id = t2.id")

    def test_quotes_handling(self):
        # Ensure that "JOIN" inside quotes isn't parsed as a keyword
        body = "t1 JOIN t2 ON t1.name = ' JOIN '"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(segments[0]["cond"], "t1.name = ' JOIN '")

    def test_parenthesized_joins(self):
        # e.g. t1 JOIN (t2 JOIN t3 ON ...) ON ...
        body = "t1 JOIN (t2 JOIN t3 ON t2.id = t3.id) sub ON t1.id = sub.id"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(segments[0]["table"], "(t2 JOIN t3 ON t2.id = t3.id) sub")

if __name__ == '__main__':
    unittest.main()
