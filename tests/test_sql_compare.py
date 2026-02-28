import unittest
from sql_compare import canonicalize_joins

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

if __name__ == '__main__':
    unittest.main()

class TestCompareSql(unittest.TestCase):
    def test_compare_sql_exact_match(self):
        from sql_compare import compare_sql
        sql = "SELECT id, name FROM users WHERE active = 1;"
        res = compare_sql(sql, sql)
        self.assertTrue(res["ws_equal"])
        self.assertTrue(res["exact_equal"])
        self.assertTrue(res["canonical_equal"])
        self.assertEqual(len(res["summary"]), 1)
        self.assertIn("No structural differences detected", res["summary"][0])

    def test_compare_sql_whitespace_diff(self):
        from sql_compare import compare_sql
        sql1 = "SELECT id, name FROM users WHERE active = 1;"
        sql2 = "  SELECT   id,   name\nFROM users \nWHERE active = 1 \n/* comment */ ;"
        res = compare_sql(sql1, sql2)
        self.assertFalse(res["ws_equal"])
        self.assertTrue(res["exact_equal"])
        self.assertTrue(res["canonical_equal"])
        self.assertEqual(len(res["summary"]), 1)
        self.assertIn("No structural differences detected", res["summary"][0])

    def test_compare_sql_canonical_match(self):
        from sql_compare import compare_sql
        sql1 = "SELECT id, name FROM users WHERE active = 1 AND role = 'admin'"
        sql2 = "SELECT name, id FROM users WHERE role = 'admin' AND active = 1"
        res = compare_sql(sql1, sql2)
        self.assertFalse(res["ws_equal"])
        self.assertFalse(res["exact_equal"])
        self.assertTrue(res["canonical_equal"])

        summary = " ".join(res["summary"])
        # Should detect differences in SELECT and WHERE order, but state they are equivalent
        self.assertIn("SELECT list order differs", summary)
        self.assertIn("WHERE AND term order differs", summary)

    def test_compare_sql_different(self):
        from sql_compare import compare_sql
        sql1 = "SELECT id FROM users WHERE active = 1"
        sql2 = "SELECT id FROM users WHERE active = 0"
        res = compare_sql(sql1, sql2)
        self.assertFalse(res["ws_equal"])
        self.assertFalse(res["exact_equal"])
        self.assertFalse(res["canonical_equal"])

        summary = " ".join(res["summary"])
        self.assertIn("Token-level changes", summary)
        self.assertNotIn("No structural differences detected", summary)

    def test_compare_sql_join_reorder_flags(self):
        from sql_compare import compare_sql
        sql1 = "SELECT * FROM t1 LEFT JOIN t2 ON x FULL OUTER JOIN t3 ON y"
        sql2 = "SELECT * FROM t1 FULL OUTER JOIN t3 ON y LEFT JOIN t2 ON x"

        # Default flags (no reordering of LEFT or FULL OUTER)
        res_default = compare_sql(sql1, sql2)
        self.assertFalse(res_default["canonical_equal"])

        # Enable LEFT and FULL OUTER reordering
        res_flags = compare_sql(sql1, sql2, allow_left=True, allow_full_outer=True)
        self.assertTrue(res_flags["canonical_equal"])
