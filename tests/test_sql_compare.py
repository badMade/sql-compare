import unittest
import sys
import os

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
