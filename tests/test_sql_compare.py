import unittest
import sys
import os

# Add parent directory to path to import sql_compare
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sql_compare import strip_sql_comments

class TestStripSQLComments(unittest.TestCase):
    def test_basic_line_comment(self):
        self.assertEqual(strip_sql_comments("SELECT 1; -- comment"), "SELECT 1; ")
        self.assertEqual(strip_sql_comments("SELECT 1;--comment"), "SELECT 1;")

    def test_basic_block_comment(self):
        self.assertEqual(strip_sql_comments("SELECT /* comment */ 1;"), "SELECT  1;")
        self.assertEqual(strip_sql_comments("SELECT/*comment*/1;"), "SELECT1;")

    def test_comment_inside_single_quotes(self):
        sql = "SELECT '/* strict */' AS s"
        self.assertEqual(strip_sql_comments(sql), sql)

    def test_comment_inside_double_quotes(self):
        sql = 'SELECT "/* strict */" AS s'
        self.assertEqual(strip_sql_comments(sql), sql)

    def test_comment_inside_brackets(self):
        sql = "SELECT [/* strict */] AS s"
        self.assertEqual(strip_sql_comments(sql), sql)

    def test_comment_inside_backticks(self):
        sql = "SELECT `/* strict */` AS s"
        self.assertEqual(strip_sql_comments(sql), sql)

    def test_dash_inside_string(self):
        sql = "SELECT '-- not a comment' AS s"
        self.assertEqual(strip_sql_comments(sql), sql)

    def test_complex_mix(self):
        sql = "SELECT 'text', /* block */ 123 -- line comment\nFROM table"
        expected = "SELECT 'text',  123 \nFROM table"
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_unterminated_block_comment(self):
        sql = "SELECT /* start"
        self.assertEqual(strip_sql_comments(sql), sql)

    def test_nested_looking_block_comment(self):
        sql = "/* comment /* nested? */ tail"
        expected = " tail"
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_escaped_brackets(self):
        # T-SQL style: [bracket] with internal bracket escaped as ]]
        # [A]]B] -> Identifier is A]B
        sql = "SELECT [A]]B] AS col"
        self.assertEqual(strip_sql_comments(sql), sql)

        # [A]] -- comment] -> Identifier is A] -- comment
        # The identifier is [A]] -- comment] which represents "A] -- comment"
        # The -- is INSIDE the identifier. So it should NOT be stripped.
        sql = "SELECT [A]] -- comment] AS col"
        self.assertEqual(strip_sql_comments(sql), sql)

    def test_escaped_backticks(self):
        # MySQL style: `backtick` with internal backtick escaped as ``
        # `A``B` -> Identifier is A`B
        sql = "SELECT `A``B` AS col"
        self.assertEqual(strip_sql_comments(sql), sql)

        # `A`` -- comment` -> Identifier is A` -- comment
        sql = "SELECT `A`` -- comment` AS col"
        self.assertEqual(strip_sql_comments(sql), sql)

if __name__ == "__main__":
    unittest.main()
