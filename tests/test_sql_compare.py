import unittest
import sys
import os

# Add parent directory to sys.path to import sql_compare
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sql_compare import compare_sql

class TestSQLCompare(unittest.TestCase):
    def test_identical(self):
        """Test that identical queries match in all modes."""
        sql = "SELECT a FROM t"
        result = compare_sql(sql, sql)
        self.assertTrue(result['ws_equal'])
        self.assertTrue(result['exact_equal'])
        self.assertTrue(result['canonical_equal'])

    def test_whitespace_only(self):
        """Test queries differing only in whitespace."""
        sql1 = "SELECT a FROM t"
        sql2 = "SELECT  a   FROM   t"
        result = compare_sql(sql1, sql2)
        # Assuming ws_only_normalize collapses whitespace
        self.assertTrue(result['ws_equal'])
        self.assertTrue(result['exact_equal'])
        self.assertTrue(result['canonical_equal'])

    def test_case_difference(self):
        """Test queries differing in case."""
        sql1 = "SELECT a FROM t"
        sql2 = "select a from t"
        result = compare_sql(sql1, sql2)
        self.assertFalse(result['ws_equal'])  # Case sensitive whitespace compare
        self.assertTrue(result['exact_equal']) # Tokens are normalized (uppercased)
        self.assertTrue(result['canonical_equal'])

    def test_canonical_select_order(self):
        """Test SELECT list reordering."""
        sql1 = "SELECT a, b FROM t"
        sql2 = "SELECT b, a FROM t"
        result = compare_sql(sql1, sql2)
        self.assertFalse(result['exact_equal'])
        self.assertTrue(result['canonical_equal'])

    def test_canonical_where_order(self):
        """Test WHERE clause AND-term reordering."""
        sql1 = "SELECT * FROM t WHERE a=1 AND b=2"
        sql2 = "SELECT * FROM t WHERE b=2 AND a=1"
        result = compare_sql(sql1, sql2)
        self.assertTrue(result['canonical_equal'])

    def test_join_reordering(self):
        """Test JOIN reordering (INNER JOINs)."""
        # Note: The current implementation only reorders subsequent joins, keeping the base table fixed.
        # So t0 JOIN t1 JOIN t2 should equal t0 JOIN t2 JOIN t1
        sql1 = "SELECT * FROM t0 JOIN t1 ON t0.id=t1.id JOIN t2 ON t0.id=t2.id"
        sql2 = "SELECT * FROM t0 JOIN t2 ON t0.id=t2.id JOIN t1 ON t0.id=t1.id"
        result = compare_sql(sql1, sql2, enable_join_reorder=True)
        self.assertTrue(result['canonical_equal'])

    def test_join_reordering_disabled(self):
        """Test that disabling join reordering prevents canonical match for reordered joins."""
        sql1 = "SELECT * FROM t0 JOIN t1 ON t0.id=t1.id JOIN t2 ON t0.id=t2.id"
        sql2 = "SELECT * FROM t0 JOIN t2 ON t0.id=t2.id JOIN t1 ON t0.id=t1.id"
        result = compare_sql(sql1, sql2, enable_join_reorder=False)
        self.assertFalse(result['canonical_equal'])

    def test_semantic_difference(self):
        """Test semantically different queries."""
        sql1 = "SELECT a FROM t"
        sql2 = "SELECT b FROM t"
        result = compare_sql(sql1, sql2)
        self.assertFalse(result['canonical_equal'])

if __name__ == '__main__':
    unittest.main()
