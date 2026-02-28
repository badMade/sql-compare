import unittest
from sql_compare import strip_sql_comments

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

if __name__ == '__main__':
    unittest.main()

from sql_compare import canonicalize_joins

class TestCanonicalizeJoins(unittest.TestCase):
    def test_canonicalize_joins_no_joins(self):
        sql = "SELECT * FROM t1"
        self.assertEqual(canonicalize_joins(sql), sql)

    def test_canonicalize_joins_single_join(self):
        sql = "SELECT * FROM t1 INNER JOIN t2 ON t1.id = t2.id"
        self.assertEqual(canonicalize_joins(sql), "SELECT * FROM t1 JOIN t2 ON t1.id = t2.id")

    def test_canonicalize_joins_reorder_inner(self):
        sql = "SELECT * FROM t1 INNER JOIN t3 ON t1.id = t3.id INNER JOIN t2 ON t1.id = t2.id"
        expected = "SELECT * FROM t1 JOIN t2 ON t1.id = t2.id JOIN t3 ON t1.id = t3.id"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_canonicalize_joins_reorder_cross(self):
        sql = "SELECT * FROM t1 CROSS JOIN t3 CROSS JOIN t2"
        expected = "SELECT * FROM t1 CROSS JOIN t2 CROSS JOIN t3"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_canonicalize_joins_reorder_natural(self):
        sql = "SELECT * FROM t1 NATURAL JOIN t3 NATURAL JOIN t2"
        expected = "SELECT * FROM t1 NATURAL JOIN t2 NATURAL JOIN t3"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_canonicalize_joins_mixed_reorderable(self):
        sql = "SELECT * FROM t1 CROSS JOIN t3 INNER JOIN t2 ON t1.id = t2.id"
        expected = "SELECT * FROM t1 CROSS JOIN t3 JOIN t2 ON t1.id = t2.id"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_canonicalize_joins_not_reordered(self):
        sql = "SELECT * FROM t1 LEFT JOIN t3 ON t1.id = t3.id INNER JOIN t2 ON t1.id = t2.id"
        self.assertEqual(canonicalize_joins(sql), "SELECT * FROM t1 LEFT JOIN t3 ON t1.id = t3.id JOIN t2 ON t1.id = t2.id")

    def test_canonicalize_joins_full_outer_allowed(self):
        sql = "SELECT * FROM t1 FULL OUTER JOIN t3 ON t1.id = t3.id FULL OUTER JOIN t2 ON t1.id = t2.id"
        expected = "SELECT * FROM t1 FULL JOIN t2 ON t1.id = t2.id FULL JOIN t3 ON t1.id = t3.id"
        self.assertEqual(canonicalize_joins(sql, allow_full_outer=True), expected)

    def test_canonicalize_joins_left_allowed(self):
        sql = "SELECT * FROM t1 LEFT JOIN t3 ON t1.id = t3.id LEFT JOIN t2 ON t1.id = t2.id"
        expected = "SELECT * FROM t1 LEFT JOIN t2 ON t1.id = t2.id LEFT JOIN t3 ON t1.id = t3.id"
        self.assertEqual(canonicalize_joins(sql, allow_left=True), expected)

    def test_canonicalize_joins_right_never_reordered(self):
        sql = "SELECT * FROM t1 RIGHT JOIN t3 ON t1.id = t3.id RIGHT JOIN t2 ON t1.id = t2.id"
        self.assertEqual(canonicalize_joins(sql), sql)
