import unittest
from sql_compare import (
    canonicalize_joins, clause_end_index, tokenize,
    strip_sql_comments, uppercase_outside_quotes,
    top_level_find_kw, remove_outer_parentheses,
    _extract_join_segments
)

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
        """Outer joins must not be reordered."""
        sql = "SELECT * FROM t1 LEFT JOIN t3 ON t1.id=t3.id LEFT JOIN t2 ON t1.id=t2.id"
        self.assertEqual(canonicalize_joins(sql), sql)

    def test_mixed_joins_reorder_only_consecutive_inner(self):
        """Reorder consecutive inner joins, but stop at outer joins."""
        sql = "SELECT * FROM t1 JOIN t3 ON t1.id=t3.id JOIN t2 ON t1.id=t2.id LEFT JOIN t4 ON t1.id=t4.id JOIN t6 ON t1.id=t6.id JOIN t5 ON t1.id=t5.id"
        expected = "SELECT * FROM t1 JOIN t2 ON t1.id=t2.id JOIN t3 ON t1.id=t3.id LEFT JOIN t4 ON t1.id=t4.id JOIN t5 ON t1.id=t5.id JOIN t6 ON t1.id=t6.id"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_subqueries_in_joins(self):
        """Should handle subqueries inside joins without messing up."""
        sql = "SELECT * FROM t1 JOIN (SELECT * FROM t3) AS sub3 ON t1.id=sub3.id JOIN t2 ON t1.id=t2.id"
        expected = "SELECT * FROM t1 JOIN t2 ON t1.id=t2.id JOIN (SELECT * FROM t3) AS sub3 ON t1.id=sub3.id"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_using_clause(self):
        """Should handle USING clauses correctly."""
        sql = "SELECT * FROM t1 JOIN t3 USING (id) JOIN t2 USING (id)"
        expected = "SELECT * FROM t1 JOIN t2 USING (id) JOIN t3 USING (id)"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_no_joins(self):
        """Should return original query if no joins exist."""
        sql = "SELECT * FROM t1 WHERE id=1"
        self.assertEqual(canonicalize_joins(sql), sql)

    def test_multiple_spaces(self):
        """Should handle multiple spaces gracefully."""
        sql = "SELECT * FROM t1   JOIN   t3 ON t1.id=t3.id  JOIN t2 ON t1.id=t2.id"
        expected = "SELECT * FROM t1 JOIN t2 ON t1.id=t2.id JOIN t3 ON t1.id=t3.id"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_join_with_aliases(self):
        """Should reorder joins including their aliases."""
        sql = "SELECT * FROM t1 JOIN table3 t3 ON t1.id=t3.id JOIN table2 t2 ON t1.id=t2.id"
        expected = "SELECT * FROM t1 JOIN table2 t2 ON t1.id=t2.id JOIN table3 t3 ON t1.id=t3.id"
        self.assertEqual(canonicalize_joins(sql), expected)


class TestClauseEndIndex(unittest.TestCase):
    def test_no_next_clause(self):
        """If there are no subsequent clauses, it should return len(tokens)."""
        tokens = [("SELECTKW", "SELECT"), ("TEXT", "*"), ("FROMKW", "FROM"), ("TEXT", "t1")]
        # Searching for the end of the FROM clause, starting at index 2
        idx = clause_end_index(tokens, 2, ["WHEREKW", "GROUPKW"])
        self.assertEqual(idx, 4)

    def test_next_clause_present(self):
        """It should return the index of the start of the next clause."""
        tokens = [
            ("SELECTKW", "SELECT"),
            ("TEXT", "*"),
            ("FROMKW", "FROM"),
            ("TEXT", "t1"),
            ("WHEREKW", "WHERE"),
            ("TEXT", "id=1")
        ]
        # Start looking at index 2 (FROMKW) for WHEREKW
        idx = clause_end_index(tokens, 2, ["WHEREKW"])
        self.assertEqual(idx, 4)

    def test_multiple_possible_next_clauses(self):
        """It should stop at the first matching next clause."""
        tokens = [
            ("SELECTKW", "SELECT"),
            ("TEXT", "*"),
            ("FROMKW", "FROM"),
            ("TEXT", "t1"),
            ("GROUPKW", "GROUP BY"),
            ("TEXT", "id")
        ]
        idx = clause_end_index(tokens, 2, ["WHEREKW", "GROUPKW", "ORDERKW"])
        self.assertEqual(idx, 4)

    def test_nested_clauses_in_parens(self):
        """It should ignore clauses that are nested inside parentheses."""
        tokens = [
            ("SELECTKW", "SELECT"),
            ("TEXT", "*"),
            ("FROMKW", "FROM"),
            ("TEXT", "("),
            ("SELECTKW", "SELECT"),
            ("TEXT", "*"),
            ("FROMKW", "FROM"),
            ("TEXT", "t2"),
            ("WHEREKW", "WHERE"),
            ("TEXT", "id=1"),
            ("TEXT", ")"),
            ("WHEREKW", "WHERE"),
            ("TEXT", "t1.id=2")
        ]
        # Look for WHEREKW starting from the first FROMKW
        idx = clause_end_index(tokens, 2, ["WHEREKW"])
        # It should skip the inner WHEREKW at index 8 and find the outer one at 11
        self.assertEqual(idx, 11)

    def test_unmatched_open_paren(self):
        """If parens are unbalanced (open but not closed), it continues to the end."""
        tokens = [
            ("FROMKW", "FROM"),
            ("TEXT", "("),
            ("WHEREKW", "WHERE")
        ]
        idx = clause_end_index(tokens, 0, ["WHEREKW"])
        self.assertEqual(idx, 3) # Reaches end because parens aren't balanced

class TestTokenize(unittest.TestCase):
    def test_basic_select_from(self):
        sql = "SELECT * FROM table1"
        expected = [
            ("SELECTKW", "SELECT "),
            ("TEXT", "* "),
            ("FROMKW", "FROM "),
            ("TEXT", "table1")
        ]
        self.assertEqual(tokenize(sql), expected)

    def test_select_where_order_by(self):
        sql = "SELECT id FROM users WHERE active=1 ORDER BY created_at"
        expected = [
            ("SELECTKW", "SELECT "),
            ("TEXT", "id "),
            ("FROMKW", "FROM "),
            ("TEXT", "users "),
            ("WHEREKW", "WHERE "),
            ("TEXT", "active=1 "),
            ("ORDERKW", "ORDER BY "),
            ("TEXT", "created_at")
        ]
        self.assertEqual(tokenize(sql), expected)

    def test_joins_and_conditions(self):
        sql = "SELECT * FROM t1 LEFT JOIN t2 ON t1.id=t2.id"
        expected = [
            ("SELECTKW", "SELECT "),
            ("TEXT", "* "),
            ("FROMKW", "FROM "),
            ("TEXT", "t1 "),
            ("JOINKW", "LEFT JOIN "),
            ("TEXT", "t2 "),
            ("CONDKW", "ON "),
            ("TEXT", "t1.id=t2.id")
        ]
        self.assertEqual(tokenize(sql), expected)

class TestClauseEndIndex(unittest.TestCase):
    def test_no_next_clause(self):
        """If there are no subsequent clauses, it should return len(tokens)."""
        tokens = [("SELECTKW", "SELECT"), ("TEXT", "*"), ("FROMKW", "FROM"), ("TEXT", "t1")]
        idx = clause_end_index(tokens, 2, ["WHEREKW", "GROUPKW"])
        self.assertEqual(idx, 4)

    def test_next_clause_present(self):
        """It should return the index of the start of the next clause."""
        tokens = [
            ("SELECTKW", "SELECT"),
            ("TEXT", "*"),
            ("FROMKW", "FROM"),
            ("TEXT", "t1"),
            ("WHEREKW", "WHERE"),
            ("TEXT", "id=1")
        ]
        idx = clause_end_index(tokens, 2, ["WHEREKW"])
        self.assertEqual(idx, 4)

    def test_multiple_possible_next_clauses(self):
        """It should stop at the first matching next clause."""
        tokens = [
            ("SELECTKW", "SELECT"),
            ("TEXT", "*"),
            ("FROMKW", "FROM"),
            ("TEXT", "t1"),
            ("GROUPKW", "GROUP BY"),
            ("TEXT", "id")
        ]
        idx = clause_end_index(tokens, 2, ["WHEREKW", "GROUPKW", "ORDERKW"])
        self.assertEqual(idx, 4)

    def test_nested_clauses_in_parens(self):
        """It should ignore clauses that are nested inside parentheses."""
        tokens = [
            ("SELECTKW", "SELECT"),
            ("TEXT", "*"),
            ("FROMKW", "FROM"),
            ("TEXT", "("),
            ("SELECTKW", "SELECT"),
            ("TEXT", "*"),
            ("FROMKW", "FROM"),
            ("TEXT", "t2"),
            ("WHEREKW", "WHERE"),
            ("TEXT", "id=1"),
            ("TEXT", ")"),
            ("WHEREKW", "WHERE"),
            ("TEXT", "t1.id=2")
        ]
        idx = clause_end_index(tokens, 2, ["WHEREKW"])
        self.assertEqual(idx, 11)

    def test_unmatched_open_paren(self):
        """If parens are unbalanced (open but not closed), it continues to the end."""
        tokens = [
            ("FROMKW", "FROM"),
            ("TEXT", "("),
            ("WHEREKW", "WHERE")
        ]
        idx = clause_end_index(tokens, 0, ["WHEREKW"])
        self.assertEqual(idx, 3)


class TestStripSqlComments(unittest.TestCase):
    def test_single_line_comment(self):
        sql = "SELECT * FROM t1 -- this is a comment\nWHERE id=1"
        expected = "SELECT * FROM t1 \nWHERE id=1"
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_multi_line_comment(self):
        sql = "SELECT * /* comment \n spanning lines */ FROM t1"
        expected = "SELECT *  FROM t1"
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_mixed_comments(self):
        sql = "SELECT * -- comment 1\n/* comment 2 */ FROM t1"
        expected = "SELECT * \n FROM t1"
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_no_comments(self):
        sql = "SELECT * FROM t1"
        expected = "SELECT * FROM t1"
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_comments_in_quotes(self):
        """Comments inside quotes should be preserved, but currently the regex removes them."""
        # Note: strip_sql_comments currently removes comments inside strings.
        # This test documents the current behavior, even if it's not ideal.
        sql = "SELECT '-- not a comment' FROM t1"
        expected = "SELECT '"
        self.assertEqual(strip_sql_comments(sql), expected)

        sql = "SELECT '/* not a comment */' FROM t1"
        expected = "SELECT '' FROM t1"
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_trailing_comment(self):
        sql = "SELECT * FROM t1 -- trailing comment"
        expected = "SELECT * FROM t1 "
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_multiple_block_comments(self):
        sql = "SELECT /* A */ * /* B */ FROM t1"
        expected = "SELECT  *  FROM t1"
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_consecutive_single_line_comments(self):
        sql = "SELECT * FROM t1\n-- comment 1\n-- comment 2\nWHERE id=1"
        expected = "SELECT * FROM t1\n\n\nWHERE id=1"
        self.assertEqual(strip_sql_comments(sql), expected)


class TestUppercaseOutsideQuotes(unittest.TestCase):
    def test_no_quotes(self):
        sql = "select * from table1"
        expected = "SELECT * FROM TABLE1"
        self.assertEqual(uppercase_outside_quotes(sql), expected)

    def test_single_quotes(self):
        sql = "select 'hello world' from table1"
        expected = "SELECT 'hello world' FROM TABLE1"
        self.assertEqual(uppercase_outside_quotes(sql), expected)

    def test_double_quotes(self):
        sql = 'select "hello world" from table1'
        expected = 'SELECT "hello world" FROM TABLE1'
        self.assertEqual(uppercase_outside_quotes(sql), expected)

    def test_escaped_single_quotes(self):
        sql = "select 'it''s escaped' from table1"
        expected = "SELECT 'it''s escaped' FROM TABLE1"
        self.assertEqual(uppercase_outside_quotes(sql), expected)

    def test_escaped_double_quotes(self):
        sql = 'select "say ""hello""" from table1'
        expected = 'SELECT "say ""hello""" FROM TABLE1'
        self.assertEqual(uppercase_outside_quotes(sql), expected)

    def test_mixed_quotes(self):
        sql = "select 'hello', \"world\" from table1"
        expected = "SELECT 'hello', \"world\" FROM TABLE1"
        self.assertEqual(uppercase_outside_quotes(sql), expected)

    def test_unclosed_quote(self):
        """If a quote is unclosed, it should stop modifying to the end."""
        sql = "select 'hello world from table1"
        expected = "SELECT 'hello world from table1"
        self.assertEqual(uppercase_outside_quotes(sql), expected)


class TestTopLevelFindKw(unittest.TestCase):
    def test_basic_find(self):
        sql = "SELECT a, b FROM table1"
        self.assertEqual(top_level_find_kw(sql, "FROM"), 12)

    def test_not_found(self):
        sql = "SELECT a, b"
        self.assertEqual(top_level_find_kw(sql, "FROM"), -1)

    def test_case_insensitivity(self):
        sql = "SELECT a, b fRoM table1"
        self.assertEqual(top_level_find_kw(sql, "FROM"), 12)

    def test_ignores_in_parentheses(self):
        sql = "SELECT (SELECT a FROM b) FROM table1"
        self.assertEqual(top_level_find_kw(sql, "FROM"), 25)

    def test_ignores_in_string_literal_single_quotes(self):
        sql = "SELECT 'str FROM str' FROM table1"
        self.assertEqual(top_level_find_kw(sql, "FROM"), 22)

    def test_ignores_in_string_literal_double_quotes(self):
        sql = 'SELECT "col FROM col" FROM table1'
        self.assertEqual(top_level_find_kw(sql, "FROM"), 22)

    def test_ignores_in_brackets(self):
        sql = "SELECT [str FROM str] FROM table1"
        self.assertEqual(top_level_find_kw(sql, "FROM"), 22)

    def test_ignores_in_backticks(self):
        sql = "SELECT `str FROM str` FROM table1"
        self.assertEqual(top_level_find_kw(sql, "FROM"), 22)

    def test_escaped_quotes(self):
        sql = "SELECT 'It''s FROM time' FROM table1"
        self.assertEqual(top_level_find_kw(sql, "FROM"), 25)

    def test_keyword_as_substring(self):
        # Should not match 'FROM' inside 'FROMPART'
        sql = "SELECT FROMPART FROM table1"
        self.assertEqual(top_level_find_kw(sql, "FROM"), 16)

    def test_multiple_occurrences(self):
        # Should return the first top-level occurrence
        sql = "SELECT a FROM table1 JOIN table2 ON a=b FROM"
        self.assertEqual(top_level_find_kw(sql, "FROM"), 9)

    def test_nested_parentheses(self):
        sql = "SELECT ((SELECT a FROM b)) FROM table1"
        self.assertEqual(top_level_find_kw(sql, "FROM"), 27)

    def test_unbalanced_parentheses(self):
        # If unbalanced, it will continue looking after the unbalanced part
        sql = "SELECT (a FROM table1"
        self.assertEqual(top_level_find_kw(sql, "FROM"), -1)

    def test_match_at_start(self):
        sql = "FROM table1"
        self.assertEqual(top_level_find_kw(sql, "FROM"), 0)

class TestSecurity(unittest.TestCase):
    def test_no_xss_in_html_report(self):
        """Ensure that HTML generation is tested for basic XSS vectors."""
        # Using a very rudimentary test, ideally we'd parse the output and assert
        # tags are escaped, but testing standard functions does this well.
        from sql_compare import generate_html_report, run_comparison

        sql1 = "<script>alert(1)</script>"
        sql2 = "SELECT 1"

        diff_info, res1, res2 = run_comparison(sql1, sql2)
        html = generate_html_report(diff_info, sql1, sql2, res1, res2)

        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_stdin_size_limit(self):
        """Ensure stdin reading is bounded."""
        from sql_compare import read_from_stdin_two_parts
        import sys
        from unittest.mock import patch, mock_open

        # Mock sys.stdin with a stream larger than the limit
        large_input = "a" * (5 * 1024 * 1024 + 10)  # slightly larger than 5MB

        with patch('sys.stdin.read', return_value=large_input):
            with self.assertRaises(ValueError) as context:
                read_from_stdin_two_parts()

            self.assertIn("Standard input exceeds size limit", str(context.exception))

class TestRemoveOuterParentheses(unittest.TestCase):
    def test_no_parentheses(self):
        self.assertEqual(remove_outer_parentheses("SELECT 1"), "SELECT 1")

    def test_single_layer(self):
        self.assertEqual(remove_outer_parentheses("(SELECT 1)"), "SELECT 1")

    def test_multiple_layers(self):
        self.assertEqual(remove_outer_parentheses("(((SELECT 1)))"), "SELECT 1")

    def test_unmatched_parentheses_1(self):
        self.assertEqual(remove_outer_parentheses("(SELECT 1"), "(SELECT 1")

    def test_unmatched_parentheses_2(self):
        self.assertEqual(remove_outer_parentheses("SELECT 1)"), "SELECT 1)")

    def test_internal_parentheses(self):
        self.assertEqual(remove_outer_parentheses("SELECT (1)"), "SELECT (1)")

    def test_partial_wrap(self):
        # E.g. (SELECT 1) UNION (SELECT 2) -> shouldn't be stripped because the outer parens don't wrap the whole string
        self.assertEqual(remove_outer_parentheses("(A) AND (B)"), "(A) AND (B)")

    def test_whitespace_handling(self):
        self.assertEqual(remove_outer_parentheses("  (  SELECT 1  )  "), "SELECT 1")

    def test_empty_string(self):
        self.assertEqual(remove_outer_parentheses("()"), "")
        self.assertEqual(remove_outer_parentheses(" ( ) "), "")


class TestExtractJoinSegments(unittest.TestCase):
    def test_extract_join_segments(self):
        test_cases = [
            (
                "Empty tokens",
                [], 0, []
            ),
            (
                "Single JOIN with ON condition",
                [
                    ("JOINKW", "JOIN"),
                    ("TEXT", "table2"),
                    ("CONDKW", "ON"),
                    ("TEXT", "t1.id = t2.id")
                ],
                0,
                [{
                    "type": "INNER",
                    "table": "table2",
                    "cond_kw": "ON",
                    "cond": "t1.id = t2.id"
                }]
            ),
            (
                "JOIN with USING condition",
                [
                    ("JOINKW", "LEFT JOIN"),
                    ("TEXT", "table3"),
                    ("CONDKW", "USING"),
                    ("TEXT", "(id)")
                ],
                0,
                [{
                    "type": "LEFT",
                    "table": "table3",
                    "cond_kw": "USING",
                    "cond": "(id)"
                }]
            ),
            (
                "Multiple joins in sequence",
                [
                    ("JOINKW", "JOIN"),
                    ("TEXT", "table2"),
                    ("CONDKW", "ON"),
                    ("TEXT", "t1.id = t2.id"),
                    ("JOINKW", "RIGHT OUTER JOIN"),
                    ("TEXT", "table3"),
                    ("CONDKW", "ON"),
                    ("TEXT", "t2.id = t3.id")
                ],
                0,
                [
                    {
                        "type": "INNER",
                        "table": "table2",
                        "cond_kw": "ON",
                        "cond": "t1.id = t2.id"
                    },
                    {
                        "type": "RIGHT",
                        "table": "table3",
                        "cond_kw": "ON",
                        "cond": "t2.id = t3.id"
                    }
                ]
            ),
            (
                "JOIN without a condition (e.g. CROSS JOIN)",
                [
                    ("JOINKW", "CROSS JOIN"),
                    ("TEXT", "table2")
                ],
                0,
                [{
                    "type": "CROSS",
                    "table": "table2",
                    "cond_kw": None,
                    "cond": ""
                }]
            ),
            (
                "Test with a non-zero start index",
                [
                    ("TEXT", "table1"),
                    ("JOINKW", "JOIN"),
                    ("TEXT", "table2"),
                    ("CONDKW", "ON"),
                    ("TEXT", "t1.id = t2.id")
                ],
                1,
                [{
                    "type": "INNER",
                    "table": "table2",
                    "cond_kw": "ON",
                    "cond": "t1.id = t2.id"
                }]
            ),
            (
                "Test ignoring non-join tokens at the beginning",
                [
                    ("TEXT", "table1"),
                    ("TEXT", "some_alias"),
                    ("JOINKW", "JOIN"),
                    ("TEXT", "table2"),
                    ("CONDKW", "ON"),
                    ("TEXT", "t1.id = t2.id")
                ],
                0,
                [{
                    "type": "INNER",
                    "table": "table2",
                    "cond_kw": "ON",
                    "cond": "t1.id = t2.id"
                }]
            ),
        ]

        for description, tokens, start_idx, expected in test_cases:
            with self.subTest(description=description):
                self.assertEqual(_extract_join_segments(tokens, start_idx), expected)


if __name__ == '__main__':
    unittest.main()
