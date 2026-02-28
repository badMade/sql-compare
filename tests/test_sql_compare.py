import unittest
from sql_compare import canonicalize_where_and

class TestCanonicalizeWhereAnd(unittest.TestCase):
    def test_basic_reordering(self):
        sql = "SELECT * FROM t WHERE B=2 AND A=1"
        expected = "SELECT * FROM t WHERE A=1 AND B=2"
        self.assertEqual(canonicalize_where_and(sql), expected)

    def test_parentheses(self):
        sql = "SELECT * FROM t WHERE (B=2) AND (A=1)"
        expected = "SELECT * FROM t WHERE (A=1) AND (B=2)"
        self.assertEqual(canonicalize_where_and(sql), expected)

    def test_nested_logic_in_parens(self):
        sql = "SELECT * FROM t WHERE (B=2 OR A=1)"
        expected = "SELECT * FROM t WHERE (B=2 OR A=1)"
        self.assertEqual(canonicalize_where_and(sql), expected)

    def test_mixed_and_or_bug(self):
        # The bug: "WHERE A=1 OR B=2 AND C=3"
        # Current behavior splits on AND at the top level and sorts, messing up OR grouping.
        # We expect it to sort the AND terms inside the OR terms, or at least not break logic.
        sql = "SELECT * FROM t WHERE Z=9 OR Y=8 AND X=7"
        # Since AND binds tighter than OR, this is: Z=9 OR (Y=8 AND X=7)
        # We expect the canonicalizer to correctly group it as an OR of two things,
        # and inside the second thing, sort the ANDs -> X=7 AND Y=8
        # And sort the ORs themselves -> X=7 AND Y=8 OR Z=9 (if ORs are sorted)
        # For now, let's just make sure it parses them correctly and outputs a valid equivalent.
        # It should probably sort the OR terms alphabetically as well:
        # Term 1: Z=9
        # Term 2: X=7 AND Y=8
        # Sorted ORs: X=7 AND Y=8 OR Z=9
        expected = "SELECT * FROM t WHERE X=7 AND Y=8 OR Z=9"
        # Or if ORs aren't sorted: Z=9 OR X=7 AND Y=8

        # Let's see what happens if we just run it and see the result
        # The test expects it to at least preserve the AND grouping properly.
        # A simpler check: does it evaluate to the same structure?

        result = canonicalize_where_and(sql)
        self.assertIn("X=7 AND Y=8", result)
        self.assertIn("Z=9", result)
        self.assertTrue(result.endswith("X=7 AND Y=8 OR Z=9") or result.endswith("Z=9 OR X=7 AND Y=8"))

    def test_multiple_ors_and_ands(self):
        sql = "SELECT * FROM t WHERE D=4 AND C=3 OR B=2 AND A=1"
        expected = "SELECT * FROM t WHERE A=1 AND B=2 OR C=3 AND D=4"
        self.assertEqual(canonicalize_where_and(sql), expected)

if __name__ == '__main__':
    unittest.main()
