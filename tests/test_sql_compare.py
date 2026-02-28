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
    def test_ws_equal(self):
        """Identical queries with different spacing should be ws_equal."""
        sql1 = "SELECT *    FROM t1"
        sql2 = "SELECT\n* FROM\n\n\nt1"
        res = compare_sql(sql1, sql2)
        self.assertTrue(res["ws_equal"])
        self.assertTrue(res["exact_equal"])
        self.assertTrue(res["canonical_equal"])

    def test_exact_equal(self):
        """Queries with different case/comments should be exact_equal but not ws_equal."""
        sql1 = "SELECT a FROM t1 -- test"
        sql2 = "select A from T1"
        res = compare_sql(sql1, sql2)
        self.assertFalse(res["ws_equal"])
        self.assertTrue(res["exact_equal"])
        self.assertTrue(res["canonical_equal"])

    def test_canonical_equal_joins(self):
        """Queries with reordered INNER JOINs should be canonical_equal but not exact_equal."""
        sql1 = "SELECT * FROM t1 JOIN t2 ON id1=id2 JOIN t3 ON id1=id3"
        sql2 = "SELECT * FROM t1 JOIN t3 ON id1=id3 JOIN t2 ON id1=id2"
        res = compare_sql(sql1, sql2)
        self.assertFalse(res["exact_equal"])
        self.assertTrue(res["canonical_equal"])

    def test_not_equal(self):
        """Queries with different tables should not be equal in any way."""
        sql1 = "SELECT * FROM t1"
        sql2 = "SELECT * FROM t2"
        res = compare_sql(sql1, sql2)
        self.assertFalse(res["ws_equal"])
        self.assertFalse(res["exact_equal"])
        self.assertFalse(res["canonical_equal"])

    def test_flags_propagation_allow_left(self):
        """LEFT JOIN reordering should only happen if allow_left=True."""
        sql1 = "SELECT * FROM t1 LEFT JOIN t2 ON id1=id2 LEFT JOIN t3 ON id1=id3"
        sql2 = "SELECT * FROM t1 LEFT JOIN t3 ON id1=id3 LEFT JOIN t2 ON id1=id2"

        # Default: shouldn't reorder LEFT JOIN
        res_default = compare_sql(sql1, sql2)
        self.assertFalse(res_default["canonical_equal"])

        # With flag: should reorder
        res_allowed = compare_sql(sql1, sql2, allow_left=True)
        self.assertTrue(res_allowed["canonical_equal"])

    def test_flags_propagation_allow_full_outer(self):
        """FULL OUTER JOIN reordering should only happen if allow_full_outer=True."""
        sql1 = "SELECT * FROM t1 FULL JOIN t2 ON id1=id2 FULL JOIN t3 ON id1=id3"
        sql2 = "SELECT * FROM t1 FULL JOIN t3 ON id1=id3 FULL JOIN t2 ON id1=id2"

        res_default = compare_sql(sql1, sql2)
        self.assertFalse(res_default["canonical_equal"])

        res_allowed = compare_sql(sql1, sql2, allow_full_outer=True)
        self.assertTrue(res_allowed["canonical_equal"])

    def test_flags_propagation_enable_join_reorder(self):
        """INNER JOIN reordering should not happen if enable_join_reorder=False."""
        sql1 = "SELECT * FROM t1 JOIN t2 ON id1=id2 JOIN t3 ON id1=id3"
        sql2 = "SELECT * FROM t1 JOIN t3 ON id1=id3 JOIN t2 ON id1=id2"

        res_disabled = compare_sql(sql1, sql2, enable_join_reorder=False)
        self.assertFalse(res_disabled["canonical_equal"])


if __name__ == '__main__':
    unittest.main()
