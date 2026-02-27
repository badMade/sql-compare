import unittest
import sys
import os

# Add parent directory to path so we can import sql_compare
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sql_compare import compare_sql

class TestSQLCompareIntegration(unittest.TestCase):

    def test_basic_equality(self):
        """Test that identical strings are equal in all modes."""
        sql = "SELECT * FROM table"
        result = compare_sql(sql, sql)
        self.assertTrue(result['ws_equal'])
        self.assertTrue(result['exact_equal'])
        self.assertTrue(result['canonical_equal'])
        self.assertEqual(len(result['summary']), 1)
        self.assertIn("No structural differences", result['summary'][0])

    def test_whitespace_normalization(self):
        """Test whitespace differences."""
        sql1 = "SELECT a, b FROM t"
        sql2 = "SELECT   a,   b   FROM   t"

        # Default: ignore_ws=False
        result = compare_sql(sql1, sql2, ignore_ws=False)
        self.assertTrue(result['ws_equal'])
        self.assertTrue(result['exact_equal']) # exact_equal tokens are same
        self.assertTrue(result['canonical_equal'])

        # ignore_ws=True
        result = compare_sql(sql1, sql2, ignore_ws=True)
        self.assertTrue(result['ws_equal'])

    def test_canonical_select_order(self):
        """Test that SELECT list order does not matter in canonical mode."""
        sql1 = "SELECT a, b, c FROM t"
        sql2 = "SELECT c, a, b FROM t"

        result = compare_sql(sql1, sql2)
        self.assertFalse(result['exact_equal'])
        self.assertTrue(result['canonical_equal'])

        # Verify summary mentions order difference if we look at norm diffs,
        # but here we are equal canonically.
        # Actually, if they are canonically equal, the summary might say so or might mention the reordering if checking intermediate steps?
        # Let's check the code: build_difference_summary compares norm_a vs norm_b and can_a vs can_b logic.
        # It checks _select_items(norm_a) vs _select_items(norm_b).
        # If sets match but order differs, it appends "SELECT list order differs".
        self.assertTrue(any("SELECT list order differs" in s for s in result['summary']))

    def test_canonical_where_order(self):
        """Test that WHERE AND terms order does not matter in canonical mode."""
        sql1 = "SELECT * FROM t WHERE x=1 AND y=2"
        sql2 = "SELECT * FROM t WHERE y=2 AND x=1"

        result = compare_sql(sql1, sql2)
        self.assertFalse(result['exact_equal'])
        self.assertTrue(result['canonical_equal'])
        self.assertTrue(any("WHERE AND term order differs" in s for s in result['summary']))

    def test_join_reordering_inner(self):
        """Test INNER JOIN reordering."""
        sql1 = "SELECT * FROM t1 JOIN t2 ON t1.id = t2.id JOIN t3 ON t2.id = t3.id"
        sql2 = "SELECT * FROM t1 JOIN t3 ON t2.id = t3.id JOIN t2 ON t1.id = t2.id"
        # Note: sql_compare reorders contiguous runs.
        # Wait, the logic in sql_compare parses FROM body.
        # t1 JOIN t2 ... JOIN t3 ...
        # If both are INNER, they can be swapped if the tool supports it.
        # Let's verify expectations for this tool.
        # The tool sorts them.

        result = compare_sql(sql1, sql2, enable_join_reorder=True)
        self.assertTrue(result['canonical_equal'])

    def test_join_reordering_disabled(self):
        """Test that join reordering can be disabled."""
        sql1 = "SELECT * FROM t1 JOIN t2 ON t1.id = t2.id JOIN t3 ON t2.id = t3.id"
        sql2 = "SELECT * FROM t1 JOIN t3 ON t2.id = t3.id JOIN t2 ON t1.id = t2.id"

        result = compare_sql(sql1, sql2, enable_join_reorder=False)
        self.assertFalse(result['canonical_equal'])
        self.assertTrue(any("Join reordering is disabled" in s for s in result['summary']))

    def test_left_join_reordering(self):
        """Test LEFT JOIN reordering (heuristic)."""
        sql1 = "SELECT * FROM t1 LEFT JOIN t2 ON c1 LEFT JOIN t3 ON c2"
        sql2 = "SELECT * FROM t1 LEFT JOIN t3 ON c2 LEFT JOIN t2 ON c1"

        # Default: allow_left=False
        result = compare_sql(sql1, sql2, enable_join_reorder=True, allow_left=False)
        self.assertFalse(result['canonical_equal'])

        # Enabled
        result = compare_sql(sql1, sql2, enable_join_reorder=True, allow_left=True)
        self.assertTrue(result['canonical_equal'])

    def test_full_join_reordering(self):
        """Test FULL OUTER JOIN reordering (heuristic)."""
        sql1 = "SELECT * FROM t1 FULL JOIN t2 ON c1 FULL JOIN t3 ON c2"
        sql2 = "SELECT * FROM t1 FULL JOIN t3 ON c2 FULL JOIN t2 ON c1"

        # Default: allow_full_outer=False
        result = compare_sql(sql1, sql2, enable_join_reorder=True, allow_full_outer=False)
        self.assertFalse(result['canonical_equal'])

        # Enabled
        result = compare_sql(sql1, sql2, enable_join_reorder=True, allow_full_outer=True)
        self.assertTrue(result['canonical_equal'])

    def test_comments_and_case(self):
        """Test comment stripping and case insensitivity (outside quotes)."""
        sql1 = "SELECT * FROM table -- comment"
        sql2 = "select * from TABLE /* block */"

        result = compare_sql(sql1, sql2)
        self.assertTrue(result['exact_equal']) # tokens should match after normalization
        self.assertTrue(result['canonical_equal'])

    def test_structure_diff(self):
        """Test summary when structure differs."""
        sql1 = "SELECT a, b FROM t"
        sql2 = "SELECT a FROM t"

        result = compare_sql(sql1, sql2)
        self.assertFalse(result['canonical_equal'])
        summary = " ".join(result['summary'])
        self.assertIn("SELECT list differs", summary)
        self.assertIn("items only in SQL1", summary)

if __name__ == '__main__':
    unittest.main()
