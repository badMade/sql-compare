import unittest
from sql_compare import canonicalize_joins, split_top_level

class TestSplitTopLevel(unittest.TestCase):
    def test_basic_split(self):
        """Basic split without quotes or brackets."""
        self.assertEqual(split_top_level("a, b, c", ","), ["a", "b", "c"])
        self.assertEqual(split_top_level("a AND b AND c", " AND "), ["a", "b", "c"])

    def test_parentheses(self):
        """Split should ignore separators inside parentheses."""
        self.assertEqual(split_top_level("a, (b, c), d", ","), ["a", "(b, c)", "d"])
        self.assertEqual(split_top_level("a AND (b AND c) AND d", " AND "), ["a", "(b AND c)", "d"])

    def test_single_quotes(self):
        """Split should ignore separators inside single quotes."""
        self.assertEqual(split_top_level("a, 'b, c', d", ","), ["a", "'b, c'", "d"])

    def test_double_quotes(self):
        """Split should ignore separators inside double quotes."""
        self.assertEqual(split_top_level('a, "b, c", d', ","), ["a", '"b, c"', "d"])

    def test_brackets(self):
        """Split should ignore separators inside square brackets."""
        self.assertEqual(split_top_level("a, [b, c], d", ","), ["a", "[b, c]", "d"])

    def test_backticks(self):
        """Split should ignore separators inside backticks."""
        self.assertEqual(split_top_level("a, `b, c`, d", ","), ["a", "`b, c`", "d"])

    def test_escaped_quotes(self):
        """Split should handle escaped quotes correctly."""
        # 'b, ''c, d'', e' should be a single string.
        self.assertEqual(split_top_level("a, 'b, ''c, d'', e', f", ","), ["a", "'b, ''c, d'', e'", "f"])
        self.assertEqual(split_top_level('a, "b, ""c, d"", e", f', ","), ["a", '"b, ""c, d"", e"', "f"])

    def test_nested_structures(self):
        """Split should handle nested parentheses and quotes."""
        self.assertEqual(split_top_level("(a, 'b, c', (d, e))", ","), ["(a, 'b, c', (d, e))"])

    def test_empty_strings(self):
        """Empty strings between consecutive separators should be dropped."""
        self.assertEqual(split_top_level("a,,b,,,c", ","), ["a", "b", "c"])
        self.assertEqual(split_top_level("  , a, b ,  ", ","), ["a", "b"])

    def test_unmatched_structures(self):
        """Should gracefully handle unmatched quotes/parentheses."""
        # Unmatched open parenthesis: it never goes back to level 0.
        self.assertEqual(split_top_level("a, (b, c", ","), ["a", "(b, c"])
        # Unmatched quote: it stays in string mode till the end.
        self.assertEqual(split_top_level("a, 'b, c", ","), ["a", "'b, c"])

class TestCanonicalizeJoins(unittest.TestCase):
    def test_basic_inner_join_reorder(self):
        """Inner joins should be reordered alphabetically by table name."""
        sql = "SELECT * FROM t1 JOIN t3 ON t1.id=t3.id JOIN t2 ON t1.id=t2.id"
        expected = "SELECT * FROM t1 JOIN t2 ON t1.id=t2.id JOIN t3 ON t1.id=t3.id"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_explicit_inner_join_reorder(self):
        """INNER JOIN keywords should be treated same as JOIN."""
        sql = "SELECT * FROM t1 INNER JOIN t3 ON t1.id=t3.id INNER JOIN t2 ON t1.id=t2.id"
        expected = "SELECT * FROM t1 JOIN t2 ON t1.id=t2.id JOIN t3 ON t1.id=t3.id"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_left_join_no_reorder(self):
        """Left joins should NOT be reordered by default."""
        sql = "SELECT * FROM t1 LEFT JOIN t3 ON t1.id=t3.id LEFT JOIN t2 ON t1.id=t2.id"
        self.assertEqual(canonicalize_joins(sql), sql)

    def test_left_join_allow_reorder(self):
        """Left joins SHOULD be reordered if allow_left is True."""
        sql = "SELECT * FROM t1 LEFT JOIN t3 ON t1.id=t3.id LEFT JOIN t2 ON t1.id=t2.id"
        expected = "SELECT * FROM t1 LEFT JOIN t2 ON t1.id=t2.id LEFT JOIN t3 ON t1.id=t3.id"
        self.assertEqual(canonicalize_joins(sql, allow_left=True), expected)

    def test_mixed_joins_barrier(self):
        """Reorderable joins should not cross non-reorderable join barriers."""
        # t3 and t2 are INNER (reorderable), t4 is LEFT (barrier)
        sql = "SELECT * FROM t1 JOIN t3 ON x JOIN t2 ON y LEFT JOIN t4 ON z"
        # t3 and t2 should swap.
        expected = "SELECT * FROM t1 JOIN t2 ON y JOIN t3 ON x LEFT JOIN t4 ON z"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_mixed_joins_barrier_2(self):
        """Reorderable joins should not cross non-reorderable join barriers (case 2)."""
        # t1 -> LEFT t2 -> JOIN t4 -> JOIN t3
        # t4 and t3 are after the barrier t2. They should be reordered among themselves.
        sql = "SELECT * FROM t1 LEFT JOIN t2 ON x JOIN t4 ON y JOIN t3 ON z"
        expected = "SELECT * FROM t1 LEFT JOIN t2 ON x JOIN t3 ON z JOIN t4 ON y"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_full_outer_join_no_reorder(self):
        """FULL OUTER joins should NOT be reordered by default."""
        sql = "SELECT * FROM t1 FULL JOIN t3 ON x FULL JOIN t2 ON y"
        self.assertEqual(canonicalize_joins(sql), sql)

    def test_full_outer_join_allow_reorder(self):
        """FULL OUTER joins SHOULD be reordered if allow_full_outer is True."""
        sql = "SELECT * FROM t1 FULL JOIN t3 ON x FULL JOIN t2 ON y"
        expected = "SELECT * FROM t1 FULL JOIN t2 ON y FULL JOIN t3 ON x"
        self.assertEqual(canonicalize_joins(sql, allow_full_outer=True), expected)

    def test_cross_join_reorder(self):
        """CROSS JOIN should be reordered."""
        sql = "SELECT * FROM t1 CROSS JOIN t3 CROSS JOIN t2"
        expected = "SELECT * FROM t1 CROSS JOIN t2 CROSS JOIN t3"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_natural_join_reorder(self):
        """NATURAL JOIN should be reordered."""
        sql = "SELECT * FROM t1 NATURAL JOIN t3 NATURAL JOIN t2"
        expected = "SELECT * FROM t1 NATURAL JOIN t2 NATURAL JOIN t3"
        self.assertEqual(canonicalize_joins(sql), expected)

if __name__ == '__main__':
    unittest.main()
