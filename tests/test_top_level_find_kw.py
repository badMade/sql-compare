import unittest
from sql_compare import top_level_find_kw

class TestTopLevelFindKw(unittest.TestCase):
    def test_basic_find(self):
        """Find simple top-level keyword."""
        sql = "SELECT * FROM users"
        # "FROM" starts at index 9
        self.assertEqual(top_level_find_kw(sql, "FROM"), 9)
        self.assertEqual(top_level_find_kw(sql, "SELECT"), 0)

    def test_case_insensitivity(self):
        """Keywords should be matched regardless of case."""
        sql = "select * from users"
        self.assertEqual(top_level_find_kw(sql, "FROM"), 9)
        self.assertEqual(top_level_find_kw(sql, "from"), 9)

    def test_ignore_single_quotes(self):
        """Keywords inside single quotes should be ignored."""
        sql = "SELECT 'hello from the other side' FROM users"
        # First 'FROM' is inside quotes, second is at index 35
        self.assertEqual(top_level_find_kw(sql, "FROM"), 35)

    def test_ignore_double_quotes(self):
        """Keywords inside double quotes should be ignored."""
        sql = 'SELECT "user from city" FROM users'
        self.assertEqual(top_level_find_kw(sql, "FROM"), 24)

    def test_ignore_backticks(self):
        """Keywords inside backticks should be ignored."""
        sql = "SELECT `select from users` FROM users"
        self.assertEqual(top_level_find_kw(sql, "FROM"), 27)

    def test_ignore_brackets(self):
        """Keywords inside brackets should be ignored."""
        sql = "SELECT [select from users] FROM users"
        self.assertEqual(top_level_find_kw(sql, "FROM"), 27)

    def test_ignore_parentheses(self):
        """Keywords inside parentheses should be ignored."""
        sql = "SELECT (SELECT id FROM other) FROM users"
        self.assertEqual(top_level_find_kw(sql, "FROM"), 30)

    def test_start_index(self):
        """Should respect start index parameter."""
        sql = "SELECT FROM a FROM b"
        # First FROM is at 7, second is at 14
        self.assertEqual(top_level_find_kw(sql, "FROM"), 7)
        self.assertEqual(top_level_find_kw(sql, "FROM", start=8), 14)

    def test_not_found(self):
        """Should return -1 when keyword is not found at top level."""
        sql = "SELECT * FROM users"
        self.assertEqual(top_level_find_kw(sql, "WHERE"), -1)

    def test_not_found_only_nested(self):
        """Should return -1 when keyword is only found inside nested context."""
        sql = "SELECT (SELECT id FROM other) AS a"
        self.assertEqual(top_level_find_kw(sql, "FROM"), -1)

    def test_word_boundary(self):
        """Should only match on word boundaries."""
        sql = "SELECT id as from_id FROM users"
        # "from_id" contains "from" but it's not a word boundary
        self.assertEqual(top_level_find_kw(sql, "FROM"), 21)

if __name__ == '__main__':
    unittest.main()
