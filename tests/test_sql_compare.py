import unittest
import sql_compare

class TestCanonicalizeWhereAnd(unittest.TestCase):
    def test_simple_and(self):
        """Test simple AND reordering (should sort)."""
        sql = "SELECT * FROM t WHERE B=1 AND A=1"
        expected = "SELECT * FROM t WHERE A=1 AND B=1"
        self.assertEqual(sql_compare.canonicalize_where_and(sql), expected)

    def test_mixed_and_or_unsafe(self):
        """Test mixed AND/OR at top level (should NOT reorder unsafely).
        Currently fails because the code reorders it incorrectly.
        Original: C=1 AND A=1 OR B=1  => (C AND A) OR B
        Incorrect canonical: A=1 OR B=1 AND C=1 => A OR (B AND C)
        """
        sql = "SELECT * FROM t WHERE C=1 AND A=1 OR B=1"
        # We expect it to remain unchanged or at least strictly equivalent.
        # Since we can't easily reorder mixed AND/OR safely without full parsing,
        # we expect it to be UNCHANGED (or at least not broken).
        # The current buggy implementation changes it to "SELECT * FROM t WHERE A=1 OR B=1 AND C=1"
        # We assert that it should remain "SELECT * FROM t WHERE C=1 AND A=1 OR B=1"
        # (assuming we disable reordering for mixed AND/OR).
        expected = "SELECT * FROM t WHERE C=1 AND A=1 OR B=1"
        self.assertEqual(sql_compare.canonicalize_where_and(sql), expected)

    def test_mixed_and_or_safe_parens(self):
        """Test mixed AND/OR where OR is inside parens (should sort the ANDs)."""
        sql = "SELECT * FROM t WHERE (A=1 OR B=1) AND C=1"
        # (A OR B) is one term. C is another.
        # Sorted: (A OR B) starts with '(', C starts with 'C'.
        # '(' (ASCII 40) vs 'C' (ASCII 67). '(' comes first.
        # So expected: "(A=1 OR B=1) AND C=1"
        expected = "SELECT * FROM t WHERE (A=1 OR B=1) AND C=1"
        self.assertEqual(sql_compare.canonicalize_where_and(sql), expected)

        # Try another order to force a swap
        sql2 = "SELECT * FROM t WHERE C=1 AND (A=1 OR B=1)"
        # Expected: "(A=1 OR B=1) AND C=1"
        self.assertEqual(sql_compare.canonicalize_where_and(sql2), expected)

    def test_nested_parens(self):
        """Test nested parentheses are preserved."""
        sql = "SELECT * FROM t WHERE ((A=1 OR B=1) AND D=1) AND C=1"
        # Terms: "((A=1 OR B=1) AND D=1)" and "C=1"
        # 'C' vs '(' -> '(' comes first.
        expected = "SELECT * FROM t WHERE ((A=1 OR B=1) AND D=1) AND C=1"
        self.assertEqual(sql_compare.canonicalize_where_and(sql), expected)

        # Also test the swapped order to ensure sorting is effective
        sql_swapped = "SELECT * FROM t WHERE C=1 AND ((A=1 OR B=1) AND D=1)"
        self.assertEqual(sql_compare.canonicalize_where_and(sql_swapped), expected)

    def test_mixed_and_or_another_unsafe(self):
        """Another unsafe mixed case: A OR B AND C"""
        sql = "SELECT * FROM t WHERE A=1 OR B=1 AND C=1"
        # Should remain unchanged if we disable reordering for mixed operators.
        expected = "SELECT * FROM t WHERE A=1 OR B=1 AND C=1"
        self.assertEqual(sql_compare.canonicalize_where_and(sql), expected)

if __name__ == '__main__':
    unittest.main()
