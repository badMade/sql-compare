import unittest
from sql_compare import strip_sql_comments
from sql_compare import canonicalize_joins

class TestStripSQLComments(unittest.TestCase):
    def test_basic_line_comment(self):
        sql = "SELECT 1; -- comment"
        expected = "SELECT 1; "
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_basic_block_comment(self):
        sql = "SELECT 1; /* comment */"
        expected = "SELECT 1; "
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_comment_at_start(self):
        sql = "-- comment\nSELECT 1;"
        expected = "\nSELECT 1;"
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_comment_at_end_no_space(self):
        sql = "SELECT 1;--"
        expected = "SELECT 1;"
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_unterminated_string_literal(self):
        sql = "SELECT 'unterminated"
        expected = "SELECT 'unterminated"
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_unterminated_block_comment(self):
        sql = "SELECT 1 /* unterminated"
        expected = "SELECT 1 "
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_crlf_line_comment(self):
        sql = "SELECT 1; -- comment\r\nSELECT 2;"
        expected = "SELECT 1; \r\nSELECT 2;"
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_no_comments(self):
        sql = "SELECT 1;"
        expected = "SELECT 1;"
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_comment_inside_single_quotes(self):
        sql = "SELECT '-- not a comment'"
        expected = "SELECT '-- not a comment'"
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_comment_inside_double_quotes(self):
        sql = 'SELECT "-- not a comment"'
        expected = 'SELECT "-- not a comment"'
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_block_comment_inside_single_quotes(self):
        sql = "SELECT '/* not a comment */'"
        expected = "SELECT '/* not a comment */'"
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_mixed_comments(self):
        sql = "SELECT 1; -- comment 1\n/* comment 2 */ SELECT 2;"
        expected = "SELECT 1; \n SELECT 2;"
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_nested_quotes(self):
        # Escaped single quote inside single quote: 'It''s a comment -- no'
        sql = "SELECT 'It''s a comment -- no'"
        expected = "SELECT 'It''s a comment -- no'"
        self.assertEqual(strip_sql_comments(sql), expected)

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
