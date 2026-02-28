import unittest
import sys
import os

# Add parent directory to path so we can import sql_compare
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sql_compare import strip_sql_comments

class TestStripSQLComments(unittest.TestCase):
    def test_strip_sql_comments(self):
        test_cases = {
            "basic_line_comment": ("SELECT 1; -- comment", "SELECT 1; "),
            "basic_block_comment": ("SELECT 1; /* comment */", "SELECT 1; "),
            "comment_at_start": ("-- comment\nSELECT 1;", "\nSELECT 1;"),
            "comment_at_end": ("SELECT 1; -- comment", "SELECT 1; "),
            "comment_inside_single_quotes": ("SELECT '-- not a comment'", "SELECT '-- not a comment'"),
            "comment_inside_double_quotes": ('SELECT "-- not a comment"', 'SELECT "-- not a comment"'),
            "block_comment_inside_single_quotes": ("SELECT '/* not a comment */'", "SELECT '/* not a comment */'"),
            "mixed_comments": ("SELECT 1; -- comment 1\n/* comment 2 */ SELECT 2;", "SELECT 1; \n SELECT 2;"),
            "nested_quotes": ("SELECT 'It''s a comment -- no'", "SELECT 'It''s a comment -- no'"),
        }

        for name, (sql, expected) in test_cases.items():
            with self.subTest(msg=name):
                self.assertEqual(strip_sql_comments(sql), expected)

if __name__ == '__main__':
    unittest.main()
