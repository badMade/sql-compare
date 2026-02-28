import unittest
import sys
import os

# Add parent directory to path so we can import sql_compare
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

    def test_comment_at_end(self):
        sql = "SELECT 1; -- comment"
        expected = "SELECT 1; "
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_comment_inside_single_quotes(self):
        # This is expected to fail with the current regex implementation
        sql = "SELECT '-- not a comment'"
        expected = "SELECT '-- not a comment'"
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_comment_inside_double_quotes(self):
        # This is expected to fail with the current regex implementation
        sql = 'SELECT "-- not a comment"'
        expected = 'SELECT "-- not a comment"'
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_block_comment_inside_single_quotes(self):
        # This is expected to fail with the current regex implementation
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
