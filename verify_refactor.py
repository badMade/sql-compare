import unittest
import sql_compare
from sql_compare import top_level_find_kw, split_top_level, _parse_from_clause_body, remove_outer_parentheses

class TestSQLRefactor(unittest.TestCase):
    def test_top_level_find_kw(self):
        # Assumes input SQL is already uppercased if looking for uppercase keywords,
        # or that exact case match is required.
        # Based on code: re.match(rf"\b{re.escape(kw)}\b", sql[i:])

        # Simple case
        self.assertEqual(top_level_find_kw("SELECT * FROM T", "FROM"), 9)

        # Ignored in quotes
        self.assertEqual(top_level_find_kw("SELECT 'FROM' FROM T", "FROM"), 14)

        # Ignored in parens
        self.assertEqual(top_level_find_kw("SELECT (SELECT 1) FROM T", "FROM"), 18)

        # Escaped quotes: 'a''b' is one string.
        # "SELECT 'a''from''b' FROM T"
        # 0123456789012345678901
        # SELECT 'a''from''b' FROM
        # Quote starts at 7. Ends at 19?
        # 'a' (8) ' (9-10 escaped) from (11-14) ' (15-16 escaped) b (17) ' (18)
        # So 'a''from''b' is the string.
        # Next FROM is at 20.
        self.assertEqual(top_level_find_kw("SELECT 'a''from''b' FROM T", "FROM"), 20)

    def test_split_top_level(self):
        self.assertEqual(split_top_level("A, B, C", ","), ["A", "B", "C"])
        self.assertEqual(split_top_level("A, 'B, C', D", ","), ["A", "'B, C'", "D"])

    def test_remove_outer_parentheses(self):
        self.assertEqual(remove_outer_parentheses("(SELECT 1)"), "SELECT 1")
        self.assertEqual(remove_outer_parentheses("(A) + (B)"), "(A) + (B)")

if __name__ == "__main__":
    unittest.main()
