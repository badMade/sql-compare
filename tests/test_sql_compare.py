import unittest
from sql_compare import canonicalize_joins, compare_sql

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
        # Note: 'FULL JOIN' is normalized to 'FULL JOIN' (OUTER is optional/removed if not handled?)
        # Let's check implementation: seg_type replaces " OUTER", so "FULL OUTER JOIN" -> "FULL JOIN".
        # Then _rebuild uses seg_type + " JOIN". So "FULL JOIN".
        # If input has "FULL OUTER JOIN", output will have "FULL JOIN".
        # We should expect "FULL JOIN".
        expected = "SELECT * FROM t1 FULL JOIN t2 ON y FULL JOIN t3 ON x"
        # However, if input is already "FULL JOIN", it stays "FULL JOIN".
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



class TestCompareSql(unittest.TestCase):
    def test_compare_sql_exact_match(self):
        sql = "SELECT a, b FROM t1"
        res = compare_sql(sql, sql)
        self.assertTrue(res["ws_equal"])
        self.assertTrue(res["exact_equal"])
        self.assertTrue(res["canonical_equal"])

    def test_compare_sql_ws_only_diff(self):
        sql1 = "SELECT a, b FROM t1"
        sql2 = "SELECT a,   b\nFROM t1"
        res = compare_sql(sql1, sql2)
        self.assertTrue(res["ws_equal"])
        self.assertTrue(res["exact_equal"])
        self.assertTrue(res["canonical_equal"])

    def test_compare_sql_case_diff(self):
        sql1 = "SELECT a, b FROM t1"
        sql2 = "select a, b from t1"
        res = compare_sql(sql1, sql2)
        self.assertFalse(res["ws_equal"])
        self.assertTrue(res["exact_equal"])
        self.assertTrue(res["canonical_equal"])

    def test_compare_sql_comment_diff(self):
        sql1 = "SELECT a, b FROM t1"
        sql2 = "SELECT a, b FROM t1 -- inline comment"
        res = compare_sql(sql1, sql2)
        self.assertFalse(res["ws_equal"])
        self.assertTrue(res["exact_equal"])
        self.assertTrue(res["canonical_equal"])

    def test_compare_sql_canonical_match(self):
        # Different order of SELECT items and WHERE ANDs
        sql1 = "SELECT a, b FROM t1 WHERE x=1 AND y=2"
        sql2 = "SELECT b, a FROM t1 WHERE y=2 AND x=1"
        res = compare_sql(sql1, sql2)
        self.assertFalse(res["ws_equal"])
        self.assertFalse(res["exact_equal"])
        self.assertTrue(res["canonical_equal"])

    def test_compare_sql_different(self):
        sql1 = "SELECT a FROM t1"
        sql2 = "SELECT b FROM t1"
        res = compare_sql(sql1, sql2)
        self.assertFalse(res["ws_equal"])
        self.assertFalse(res["exact_equal"])
        self.assertFalse(res["canonical_equal"])

    def test_compare_sql_join_reorder_flags(self):
        sql1 = "SELECT * FROM t1 JOIN t3 ON id3 JOIN t2 ON id2"
        sql2 = "SELECT * FROM t1 JOIN t2 ON id2 JOIN t3 ON id3"

        # With reorder enabled (default)
        res_enabled = compare_sql(sql1, sql2, enable_join_reorder=True)
        self.assertTrue(res_enabled["canonical_equal"])

        # With reorder disabled
        res_disabled = compare_sql(sql1, sql2, enable_join_reorder=False)
        self.assertFalse(res_disabled["canonical_equal"])

    def test_compare_sql_dict_structure(self):
        sql1 = "SELECT a FROM t"
        sql2 = "SELECT a FROM t"
        res = compare_sql(sql1, sql2)

        expected_keys = {
            "ws_a", "ws_b", "ws_equal", "diff_ws",
            "norm_a", "norm_b", "tokens_a", "tokens_b",
            "exact_equal", "diff_norm",
            "can_a", "can_b", "canonical_equal", "diff_can",
            "summary"
        }
        self.assertTrue(expected_keys.issubset(res.keys()))
        self.assertIsInstance(res["summary"], list)

if __name__ == '__main__':
    unittest.main()
