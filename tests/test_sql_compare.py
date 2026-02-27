import unittest
import sys
import os

# Add parent directory to path to import sql_compare
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sql_compare import canonicalize_joins

class TestCanonicalizeJoins(unittest.TestCase):
    def test_basic_inner_join_reorder(self):
        """Inner joins should be reordered alphabetically by table name."""
        sql = "SELECT * FROM t1 JOIN t3 ON t1.id=t3.id JOIN t2 ON t1.id=t2.id"
        expected = "SELECT * FROM t1 JOIN t2 ON t1.id=t2.id JOIN t3 ON t1.id=t3.id"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_explicit_inner_join_reorder(self):
        """INNER JOIN keywords should be treated same as JOIN."""
        sql = "SELECT * FROM t1 INNER JOIN t3 ON t1.id=t3.id INNER JOIN t2 ON t1.id=t2.id"
        expected = "SELECT * FROM t1 JOIN t2 ON t1.id=t2.id JOIN t3 ON t1.id=t3.id"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_left_join_no_reorder(self):
        """Left joins should NOT be reordered by default."""
        sql = "SELECT * FROM t1 LEFT JOIN t3 ON t1.id=t3.id LEFT JOIN t2 ON t1.id=t2.id"
        self.assertEqual(canonicalize_joins(sql), sql)

    def test_left_join_allow_reorder(self):
        """Left joins SHOULD be reordered if allow_left is True."""
        sql = "SELECT * FROM t1 LEFT JOIN t3 ON t1.id=t3.id LEFT JOIN t2 ON t1.id=t2.id"
        expected = "SELECT * FROM t1 LEFT JOIN t2 ON t1.id=t2.id LEFT JOIN t3 ON t1.id=t3.id"
        self.assertEqual(canonicalize_joins(sql, allow_left=True), expected)

    def test_mixed_joins_barrier(self):
        """Reorderable joins should not cross non-reorderable join barriers."""
        # t3 and t2 are INNER (reorderable), t4 is LEFT (barrier)
        sql = "SELECT * FROM t1 JOIN t3 ON x JOIN t2 ON y LEFT JOIN t4 ON z"
        # t3 and t2 should swap.
        expected = "SELECT * FROM t1 JOIN t2 ON y JOIN t3 ON x LEFT JOIN t4 ON z"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_mixed_joins_barrier_2(self):
        """Reorderable joins should not cross non-reorderable join barriers (case 2)."""
        # t1 -> LEFT t2 -> JOIN t4 -> JOIN t3
        # t4 and t3 are after the barrier t2. They should be reordered among themselves.
        sql = "SELECT * FROM t1 LEFT JOIN t2 ON x JOIN t4 ON y JOIN t3 ON z"
        expected = "SELECT * FROM t1 LEFT JOIN t2 ON x JOIN t3 ON z JOIN t4 ON y"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_full_outer_join_no_reorder(self):
        """FULL OUTER joins should NOT be reordered by default."""
        sql = "SELECT * FROM t1 FULL JOIN t3 ON x FULL JOIN t2 ON y"
        self.assertEqual(canonicalize_joins(sql), sql)

    def test_full_outer_join_allow_reorder(self):
        """FULL OUTER joins SHOULD be reordered if allow_full_outer is True."""
        sql = "SELECT * FROM t1 FULL JOIN t3 ON x FULL JOIN t2 ON y"
        # Note: 'FULL JOIN' is normalized to 'FULL JOIN' (OUTER is optional/removed if not handled?)
        # Let's check implementation: seg_type replaces " OUTER", so "FULL OUTER JOIN" -> "FULL JOIN".
        # Then _rebuild uses seg_type + " JOIN". So "FULL JOIN".
        # If input has "FULL OUTER JOIN", output will have "FULL JOIN".
        # We should expect "FULL JOIN".
        expected = "SELECT * FROM t1 FULL JOIN t2 ON y FULL JOIN t3 ON x"
        # However, if input is already "FULL JOIN", it stays "FULL JOIN".
        self.assertEqual(canonicalize_joins(sql, allow_full_outer=True), expected)

    def test_cross_join_reorder(self):
        """CROSS JOIN should be reordered."""
        sql = "SELECT * FROM t1 CROSS JOIN t3 CROSS JOIN t2"
        expected = "SELECT * FROM t1 CROSS JOIN t2 CROSS JOIN t3"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_natural_join_reorder(self):
        """NATURAL JOIN should be reordered."""
        sql = "SELECT * FROM t1 NATURAL JOIN t3 NATURAL JOIN t2"
        expected = "SELECT * FROM t1 NATURAL JOIN t2 NATURAL JOIN t3"
        self.assertEqual(canonicalize_joins(sql), expected)
# Add the parent directory to sys.path so we can import sql_compare
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sql_compare import remove_outer_parentheses

class TestRemoveOuterParentheses(unittest.TestCase):
    def test_basic_removal(self):
        # Basic wrapping
        self.assertEqual(remove_outer_parentheses("(foo)"), "foo")
        # Double wrapping
        self.assertEqual(remove_outer_parentheses("((foo))"), "foo")
        # Triple wrapping
        self.assertEqual(remove_outer_parentheses("(((foo)))"), "foo")
        # Whitespace stripping handled by the function
        self.assertEqual(remove_outer_parentheses(" (foo) "), "foo")

    def test_no_removal(self):
        # No parens
        self.assertEqual(remove_outer_parentheses("foo"), "foo")
        # Partial wrapping
        self.assertEqual(remove_outer_parentheses("(foo) bar"), "(foo) bar")
        # Two disjoint groups
        self.assertEqual(remove_outer_parentheses("(foo) (bar)"), "(foo) (bar)")
        # Statement like select * from (t)
        self.assertEqual(remove_outer_parentheses("select * from (t)"), "select * from (t)")

    def test_quotes_and_literals(self):
        # Paren inside single quotes
        self.assertEqual(remove_outer_parentheses("(select ')')"), "select ')'")
        # Paren inside double quotes
        self.assertEqual(remove_outer_parentheses('(select ")")'), 'select ")"')
        # Paren inside brackets
        self.assertEqual(remove_outer_parentheses("(select [)])"), "select [)]")
        # Paren inside backticks
        self.assertEqual(remove_outer_parentheses("(select `)`)"), "select `)`")

    def test_escaped_quotes(self):
        # Escaped single quote: 'O''Brian'
        self.assertEqual(remove_outer_parentheses("(select 'O''Brian')"), "select 'O''Brian'")
        # Escaped double quote: "He said ""Hello"""
        self.assertEqual(remove_outer_parentheses('(select "He said ""Hello""")'), 'select "He said ""Hello"""')

    def test_complex_nesting(self):
        # Balanced nesting: ((a + (b * c))) -> a + (b * c)
        self.assertEqual(remove_outer_parentheses("((a + (b * c)))"), "a + (b * c)")

        # (A) AND (B) -> not wrapped as a whole
        self.assertEqual(remove_outer_parentheses("(A) AND (B)"), "(A) AND (B)")

        # (A + (B)) -> A + (B)
        self.assertEqual(remove_outer_parentheses("(A + (B))"), "A + (B)")

    def test_unbalanced_input(self):
        # Starts with ( but doesn't end with )
        self.assertEqual(remove_outer_parentheses("("), "(")
        # Ends with ) but doesn't start with (
        self.assertEqual(remove_outer_parentheses(")"), ")")
        # Balanced but disjoint: ()()
        self.assertEqual(remove_outer_parentheses("()()"), "()()")

        # Unbalanced parens inside: ( ( )
        self.assertEqual(remove_outer_parentheses("( ( )"), "( ( )")

if __name__ == '__main__':
    unittest.main()
