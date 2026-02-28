import unittest
from sql_compare import canonicalize_where_and

class TestCanonicalizeWhereAnd(unittest.TestCase):
    def test_no_where_clause(self):
        """Should return the same string if there is no WHERE clause."""
        sql = "SELECT * FROM users"
        self.assertEqual(canonicalize_where_and(sql), "SELECT * FROM users")

    def test_single_condition(self):
        """Should not modify a WHERE clause with only one condition."""
        sql = "SELECT * FROM users WHERE age > 18"
        self.assertEqual(canonicalize_where_and(sql), "SELECT * FROM users WHERE age > 18")

    def test_multiple_conditions_out_of_order(self):
        """Should sort multiple AND conditions alphabetically."""
        sql = "SELECT * FROM users WHERE status = 'active' AND age > 18 AND id = 5"
        expected = "SELECT * FROM users WHERE age > 18 AND id = 5 AND status = 'active'"
        self.assertEqual(canonicalize_where_and(sql), expected)

    def test_varying_whitespace(self):
        """Should handle and normalize varying whitespace between conditions."""
        sql = "SELECT * FROM users WHERE   status = 'active'    AND age > 18 \n AND \t id = 5"
        expected = "SELECT * FROM users WHERE age > 18 AND id = 5 AND status = 'active'"
        self.assertEqual(canonicalize_where_and(sql), expected)

    def test_nested_parentheses(self):
        """Should not split on ANDs inside parentheses."""
        sql = "SELECT * FROM users WHERE status = 'active' AND (age > 18 AND age < 65) AND id = 5"
        expected = "SELECT * FROM users WHERE (age > 18 AND age < 65) AND id = 5 AND status = 'active'"
        self.assertEqual(canonicalize_where_and(sql), expected)

    def test_nested_where_clause(self):
        """Should only sort conditions in the top-level WHERE clause, ignoring subqueries."""
        sql = "SELECT * FROM users WHERE status = 'active' AND id IN (SELECT user_id FROM orders WHERE b > 1 AND a > 1) AND age > 18"
        expected = "SELECT * FROM users WHERE age > 18 AND id IN (SELECT user_id FROM orders WHERE b > 1 AND a > 1) AND status = 'active'"
        self.assertEqual(canonicalize_where_and(sql), expected)

    def test_quotes(self):
        """Should not split on AND inside string literals."""
        sql = "SELECT * FROM users WHERE name = 'Tom AND Jerry' AND age > 18"
        expected = "SELECT * FROM users WHERE age > 18 AND name = 'Tom AND Jerry'"
        self.assertEqual(canonicalize_where_and(sql), expected)

if __name__ == '__main__':
    unittest.main()
