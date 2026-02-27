import unittest
import sys
import os

# Add parent directory to path so we can import sql_compare
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sql_compare import canonicalize_joins, normalize_sql

class TestCanonicalizeJoins(unittest.TestCase):
    def test_no_joins(self):
        sql = "SELECT * FROM t1"
        expected = normalize_sql(sql)
        self.assertEqual(canonicalize_joins(expected), expected)

    def test_inner_joins_reorder(self):
        # Should be sorted by table name then condition
        # 'INNER' type outputs as 'JOIN'
        sql = "SELECT * FROM t1 INNER JOIN t3 ON t1.id=t3.id INNER JOIN t2 ON t1.id=t2.id"
        normalized = normalize_sql(sql)
        result = canonicalize_joins(normalized)
        # Expected: t2 comes before t3
        expected_fragment = "JOIN T2 ON T1.ID=T2.ID JOIN T3 ON T1.ID=T3.ID"
        self.assertIn(expected_fragment, result)

    def test_cross_natural_joins(self):
        # CROSS and NATURAL should be treated as reorderable with INNER
        # 'INNER' outputs as 'JOIN'
        sql2 = "SELECT * FROM t1 INNER JOIN t4 ON 1=1 CROSS JOIN t3 NATURAL JOIN t2"
        # Sort order:
        # CROSS < JOIN (INNER) < NATURAL

        normalized2 = normalize_sql(sql2)
        result2 = canonicalize_joins(normalized2)
        expected = "CROSS JOIN T3 JOIN T4 ON 1=1 NATURAL JOIN T2"
        self.assertIn(expected, result2)

    def test_left_join_barrier(self):
        # LEFT JOIN should stop reordering of previous INNER joins with subsequent ones
        sql = "SELECT * FROM t1 INNER JOIN t3 ON 1=1 INNER JOIN t2 ON 1=1 LEFT JOIN t4 ON 1=1 INNER JOIN t6 ON 1=1 INNER JOIN t5 ON 1=1"
        normalized = normalize_sql(sql)
        result = canonicalize_joins(normalized, allow_left=False)

        # t2 should be before t3
        self.assertIn("JOIN T2 ON 1=1 JOIN T3 ON 1=1", result)
        # t5 should be before t6
        self.assertIn("JOIN T5 ON 1=1 JOIN T6 ON 1=1", result)

        # Check that T2 and T3 are BEFORE T4
        p_t2 = result.find("JOIN T2")
        p_t3 = result.find("JOIN T3")
        p_t4 = result.find("LEFT JOIN T4")
        p_t5 = result.find("JOIN T5")
        p_t6 = result.find("JOIN T6")

        self.assertTrue(p_t2 < p_t4)
        self.assertTrue(p_t3 < p_t4)
        self.assertTrue(p_t4 < p_t5)
        self.assertTrue(p_t4 < p_t6)

    def test_right_join_barrier(self):
        # RIGHT JOIN is never reorderable.
        sql = "SELECT * FROM t1 INNER JOIN t3 ON 1=1 RIGHT JOIN t2 ON 1=1 INNER JOIN t4 ON 1=1"
        normalized = normalize_sql(sql)
        result = canonicalize_joins(normalized)

        # t3 stays before RIGHT JOIN T2. t4 stays after.
        # No sorting across RIGHT JOIN.
        self.assertIn("JOIN T3 ON 1=1 RIGHT JOIN T2 ON 1=1 JOIN T4", result)

    def test_full_join_barrier(self):
        # FULL JOIN barrier when allow_full_outer=False
        sql = "SELECT * FROM t1 INNER JOIN t3 ON 1=1 FULL OUTER JOIN t2 ON 1=1 INNER JOIN t4 ON 1=1"
        normalized = normalize_sql(sql)
        result = canonicalize_joins(normalized, allow_full_outer=False)

        self.assertIn("JOIN T3 ON 1=1 FULL JOIN T2 ON 1=1 JOIN T4", result)

    def test_allow_left(self):
        # With allow_left=True, LEFT JOINs should participate in sorting
        sql = "SELECT * FROM t1 LEFT JOIN t3 ON 1=1 INNER JOIN t2 ON 1=1"
        normalized = normalize_sql(sql)
        result = canonicalize_joins(normalized, allow_left=True)

        # Sort key: INNER < LEFT. So T2 (INNER) should come before T3 (LEFT).
        self.assertIn("JOIN T2 ON 1=1 LEFT JOIN T3 ON 1=1", result)

    def test_allow_full(self):
        # With allow_full_outer=True, FULL JOINs should participate in sorting
        # Input order: INNER JOIN T2, FULL JOIN T3.
        # Expected sort order: FULL JOIN T3 < INNER JOIN T2 (F < I)
        # So we expect them to SWAP from input order.
        sql = "SELECT * FROM t1 INNER JOIN t2 ON 1=1 FULL JOIN t3 ON 1=1"
        normalized = normalize_sql(sql)
        result = canonicalize_joins(normalized, allow_full_outer=True)

        self.assertIn("FULL JOIN T3 ON 1=1 JOIN T2 ON 1=1", result)

    def test_mixed_barriers(self):
        # t3, t2 -> sort (t2, t3)
        # RIGHT -> barrier
        # t5, t4 -> sort (t4, t5)
        sql = "SELECT * FROM t1 INNER JOIN t3 ON 1=1 INNER JOIN t2 ON 1=1 RIGHT JOIN barrier ON 1=1 INNER JOIN t5 ON 1=1 INNER JOIN t4 ON 1=1"
        normalized = normalize_sql(sql)
        result = canonicalize_joins(normalized)

        expected = "JOIN T2 ON 1=1 JOIN T3 ON 1=1 RIGHT JOIN BARRIER ON 1=1 JOIN T4 ON 1=1 JOIN T5 ON 1=1"
        self.assertIn(expected, result)

if __name__ == '__main__':
    unittest.main()
