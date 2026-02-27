import unittest
from sql_compare import compare_sql

class TestSQLCompare(unittest.TestCase):
    def test_identity(self):
        sql = "SELECT * FROM t"
        res = compare_sql(sql, sql)
        self.assertTrue(res['ws_equal'])
        self.assertTrue(res['exact_equal'])
        self.assertTrue(res['canonical_equal'])

    def test_whitespace(self):
        sql1 = "SELECT * FROM t"
        sql2 = "SELECT    *   FROM    t"
        res = compare_sql(sql1, sql2)
        self.assertTrue(res['ws_equal'])
        self.assertTrue(res['exact_equal'])
        self.assertTrue(res['canonical_equal'])

    def test_case_comments(self):
        sql1 = "SELECT * FROM t"
        sql2 = "select * from t -- comment"
        res = compare_sql(sql1, sql2)
        self.assertFalse(res['ws_equal'])
        self.assertTrue(res['exact_equal'])
        self.assertTrue(res['canonical_equal'])

    def test_canonical_select(self):
        sql1 = "SELECT a, b FROM t"
        sql2 = "SELECT b, a FROM t"
        res = compare_sql(sql1, sql2)
        # Note: exact_equal should be False because tokens differ in order
        self.assertFalse(res['exact_equal'])
        self.assertTrue(res['canonical_equal'])

    def test_canonical_where(self):
        sql1 = "SELECT * FROM t WHERE x=1 AND y=2"
        sql2 = "SELECT * FROM t WHERE y=2 AND x=1"
        res = compare_sql(sql1, sql2)
        self.assertFalse(res['exact_equal'])
        self.assertTrue(res['canonical_equal'])

    def test_join_reordering(self):
        # INNER JOINs should reorder by default
        # Let's try explicit INNER JOIN syntax to be safe, though default is INNER.
        sql1 = "SELECT * FROM base INNER JOIN t1 ON 1=1 INNER JOIN t2 ON 1=1"
        sql2 = "SELECT * FROM base INNER JOIN t2 ON 1=1 INNER JOIN t1 ON 1=1"

        res = compare_sql(sql1, sql2, enable_join_reorder=True)
        self.assertTrue(res['canonical_equal'])

        res_disable = compare_sql(sql1, sql2, enable_join_reorder=False)
        self.assertFalse(res_disable['canonical_equal'])

    def test_left_join_heuristic(self):
        # LEFT JOINs only reorder if allow_left is True
        sql1 = "SELECT * FROM base LEFT JOIN t1 ON 1=1 LEFT JOIN t2 ON 1=1"
        sql2 = "SELECT * FROM base LEFT JOIN t2 ON 1=1 LEFT JOIN t1 ON 1=1"

        # Default behavior: no reorder
        res_def = compare_sql(sql1, sql2, allow_left=False)
        self.assertFalse(res_def['canonical_equal'])

        # Allowed behavior
        res_opt = compare_sql(sql1, sql2, allow_left=True)
        self.assertTrue(res_opt['canonical_equal'])

    def test_full_join_heuristic(self):
        # FULL JOINs only reorder if allow_full_outer is True
        sql1 = "SELECT * FROM base FULL JOIN t1 ON 1=1 FULL JOIN t2 ON 1=1"
        sql2 = "SELECT * FROM base FULL JOIN t2 ON 1=1 FULL JOIN t1 ON 1=1"

        res_def = compare_sql(sql1, sql2, allow_full_outer=False)
        self.assertFalse(res_def['canonical_equal'])

        res_opt = compare_sql(sql1, sql2, allow_full_outer=True)
        self.assertTrue(res_opt['canonical_equal'])

if __name__ == '__main__':
    unittest.main()
