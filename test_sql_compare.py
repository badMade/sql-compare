import unittest
from sql_compare import uppercase_outside_quotes

class TestUppercaseOutsideQuotes(unittest.TestCase):
    def test_basic_uppercase(self):
        """Test that unquoted text is uppercased."""
        self.assertEqual(uppercase_outside_quotes("select * from table"), "SELECT * FROM TABLE")

    def test_single_quotes(self):
        """Test that content inside single quotes is preserved."""
        test_cases = [
            ("select 'Val'", "SELECT 'Val'"),
            ("'hello world'", "'hello world'"),
        ]
        for sql_input, expected in test_cases:
            with self.subTest(sql_input=sql_input):
                self.assertEqual(uppercase_outside_quotes(sql_input), expected)

    def test_double_quotes(self):
        """Test that content inside double quotes is preserved."""
        test_cases = [
            ('select "Val"', 'SELECT "Val"'),
            ('"hello world"', '"hello world"'),
        ]
        for sql_input, expected in test_cases:
            with self.subTest(sql_input=sql_input):
                self.assertEqual(uppercase_outside_quotes(sql_input), expected)

    def test_brackets(self):
        """Test that content inside brackets is preserved."""
        test_cases = [
            ("select [Val]", "SELECT [Val]"),
            ("[hello world]", "[hello world]"),
        ]
        for sql_input, expected in test_cases:
            with self.subTest(sql_input=sql_input):
                self.assertEqual(uppercase_outside_quotes(sql_input), expected)

    def test_backticks(self):
        """Test that content inside backticks is preserved."""
        test_cases = [
            ("select `Val`", "SELECT `Val`"),
            ("`hello world`", "`hello world`"),
        ]
        for sql_input, expected in test_cases:
            with self.subTest(sql_input=sql_input):
                self.assertEqual(uppercase_outside_quotes(sql_input), expected)

    def test_escaped_single_quotes(self):
        """Test escaped single quotes (doubled single quotes)."""
        self.assertEqual(uppercase_outside_quotes("select 'it''s'"), "SELECT 'it''s'")

    def test_escaped_double_quotes(self):
        """Test escaped double quotes (doubled double quotes)."""
        self.assertEqual(uppercase_outside_quotes('select "says ""hello"""'), 'SELECT "says ""hello"""')

    def test_mixed_quotes(self):
        """Test mixed usage of quotes."""
        sql = "select 'Val' as \"Alias\", [Col] from `Table` where x='y'"
        expected = "SELECT 'Val' AS \"Alias\", [Col] FROM `Table` WHERE X='y'"
        self.assertEqual(uppercase_outside_quotes(sql), expected)

    def test_empty_string(self):
        """Test empty string input."""
        self.assertEqual(uppercase_outside_quotes(""), "")

    def test_nested_looking_quotes(self):
        """Test quotes inside other quote types (should be treated as literal chars)."""
        test_cases = [
            ("select '\"'", "SELECT '\"'"),
            ('select "\'"', 'SELECT "\'"'),
        ]
        for sql_input, expected in test_cases:
            with self.subTest(sql_input=sql_input):
                self.assertEqual(uppercase_outside_quotes(sql_input), expected)

if __name__ == '__main__':
    unittest.main()
