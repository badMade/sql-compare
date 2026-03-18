import unittest
import argparse
from unittest.mock import patch
from sql_compare import (
    canonicalize_joins, clause_end_index, tokenize,
    strip_sql_comments, uppercase_outside_quotes,
    top_level_find_kw, collapse_whitespace,
    _tokenize_from_clause_body,
)


class TestCollapseWhitespace(unittest.TestCase):
    def test_collapse_whitespace_edge_cases(self):
        """Test edge cases for collapse_whitespace function."""
        test_cases = [
            # description, input_string, expected_output
            ("Empty string", "", ""),
            ("String with only spaces", "     ", ""),
            ("String with only newlines and tabs", "\n\n\t\t\n", ""),
            ("Already collapsed string", "SELECT a FROM b", "SELECT a FROM b"),
            ("Mixed whitespace characters", "SELECT\t\ta\nFROM \r\nb", "SELECT a FROM b"),
            ("Leading and trailing whitespace", "  SELECT a FROM b  ", "SELECT a FROM b"),
            ("Multiple consecutive spaces", "SELECT    a    FROM     b", "SELECT a FROM b"),
            ("Unicode whitespace", "SELECT\u00A0a\u2003FROM\u2009b", "SELECT a FROM b"),
        ]

        for description, input_str, expected in test_cases:
            with self.subTest(description=description, input=input_str):
                self.assertEqual(collapse_whitespace(input_str), expected)


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

    def test_using_clause_reorder(self):
        """USING clauses are preserved correctly when joins are reordered."""
        sql = "SELECT * FROM t1 JOIN t3 USING (id) JOIN t2 USING (id)"
        expected = "SELECT * FROM t1 JOIN t2 USING (id) JOIN t3 USING (id)"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_single_quoted_join_keyword_in_condition(self):
        """JOIN keyword inside a single-quoted string in a condition should not be
        treated as a join separator — the outer joins must still be reordered."""
        sql = "SELECT * FROM t1 JOIN t3 ON t1.name = 'JOIN me' JOIN t2 ON t1.id = t2.id"
        expected = "SELECT * FROM t1 JOIN t2 ON t1.id = t2.id JOIN t3 ON t1.name = 'JOIN me'"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_bracketed_keyword_as_table_name(self):
        """A bracketed keyword used as a table name (e.g. [ON]) must not be
        misinterpreted as a SQL keyword — outer joins must still be reordered."""
        sql = "SELECT * FROM t1 JOIN [ON] ON t1.id = [ON].id JOIN t0 ON t1.id = t0.id"
        # "[ON]" sorts after "t0" because "[" (ASCII 91) > "T" (ASCII 84)
        expected = "SELECT * FROM t1 JOIN t0 ON t1.id = t0.id JOIN [ON] ON t1.id = [ON].id"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_backtick_keyword_as_table_name(self):
        """A backtick-quoted keyword used as a table name (e.g. `JOIN`) must not be
        misinterpreted as a SQL keyword — outer joins must still be reordered."""
        sql = "SELECT * FROM t1 JOIN `JOIN` ON t1.id = `JOIN`.id JOIN t0 ON t1.id = t0.id"
        # "`JOIN`" sorts after "t0" because "`" (ASCII 96) > "T" (ASCII 84)
        expected = "SELECT * FROM t1 JOIN t0 ON t1.id = t0.id JOIN `JOIN` ON t1.id = `JOIN`.id"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_derived_table_subquery_reorder(self):
        """JOIN/ON inside a parenthesized derived table should be treated as part of
        the table expression and must not interfere with top-level join reordering."""
        sql = (
            "SELECT * FROM t1 "
            "JOIN tz ON t1.id = tz.id "
            "JOIN (SELECT a FROM t2 JOIN t3 ON t2.id = t3.id) sub ON t1.id = sub.id"
        )
        # "(SELECT..." sorts before "tz" because "(" (ASCII 40) < "T" (ASCII 84)
        expected = (
            "SELECT * FROM t1 "
            "JOIN (SELECT a FROM t2 JOIN t3 ON t2.id = t3.id) sub ON t1.id = sub.id "
            "JOIN tz ON t1.id = tz.id"
        )
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_derived_table_inner_joins_not_split_out(self):
        """Inner JOINs inside a derived table must not appear as separate top-level
        join segments — only the two outer JOINs should be present after reordering."""
        sql = (
            "SELECT * FROM t1 "
            "JOIN tz ON t1.id = tz.id "
            "JOIN (SELECT a FROM inner1 JOIN inner2 ON inner1.id = inner2.id) sub "
            "ON t1.id = sub.id"
        )
        result = canonicalize_joins(sql)
        # The subquery body must be preserved as a single unit
        self.assertIn("(SELECT a FROM inner1 JOIN inner2 ON inner1.id = inner2.id)", result)
        # inner1 and inner2 must not appear as standalone top-level join targets
        # (i.e. there should be exactly 3 JOIN occurrences: 2 outer + 1 inside the subquery)
        self.assertEqual(result.upper().count("JOIN"), 3)


class TestTokenizeFromClauseBodyEdgeCases(unittest.TestCase):
    """Unit tests for _tokenize_from_clause_body, focusing on edge cases where
    SQL keywords appear inside quoted identifiers or parenthesized subqueries."""

    def _token_kinds(self, tokens):
        """Return only the token-kind portion of each token."""
        return [k for k, _ in tokens]

    def test_basic_single_join(self):
        """Simple JOIN/ON produces TEXT, JOINKW, TEXT, CONDKW, TEXT."""
        tokens = _tokenize_from_clause_body("t1 JOIN t2 ON t1.id = t2.id")
        self.assertEqual(self._token_kinds(tokens), ["TEXT", "JOINKW", "TEXT", "CONDKW", "TEXT"])

    def test_join_on_inside_subquery_not_top_level(self):
        """JOIN and ON inside a parenthesized subquery must not be emitted as
        top-level JOINKW/CONDKW tokens (level > 0 while inside the parens)."""
        body = "t1 JOIN (SELECT * FROM t2 JOIN t3 ON t2.id = t3.id) sub ON t1.id = sub.id"
        tokens = _tokenize_from_clause_body(body)
        self.assertEqual(sum(1 for k, _ in tokens if k == "JOINKW"), 1,
                         "Expected exactly one top-level JOINKW")
        self.assertEqual(sum(1 for k, _ in tokens if k == "CONDKW"), 1,
                         "Expected exactly one top-level CONDKW")

    def test_join_inside_deeply_nested_parens_ignored(self):
        """JOIN inside multiply-nested parentheses must not become a top-level token."""
        body = "t1 JOIN ((SELECT * FROM t2 JOIN t3 ON t2.id = t3.id)) sub ON t1.id = sub.id"
        tokens = _tokenize_from_clause_body(body)
        self.assertEqual(sum(1 for k, _ in tokens if k == "JOINKW"), 1)
        self.assertEqual(sum(1 for k, _ in tokens if k == "CONDKW"), 1)

    def test_keyword_inside_single_quotes_ignored(self):
        """JOIN and ON keywords inside a single-quoted string literal must not
        produce extra JOINKW or CONDKW tokens."""
        body = "t1 JOIN t2 ON t1.name = 'JOIN ON USING'"
        tokens = _tokenize_from_clause_body(body)
        self.assertEqual(sum(1 for k, _ in tokens if k == "JOINKW"), 1)
        self.assertEqual(sum(1 for k, _ in tokens if k == "CONDKW"), 1)

    def test_keyword_inside_double_quotes_ignored(self):
        """A double-quoted identifier containing a SQL keyword must not produce an
        extra JOINKW token; the quoted string is captured as part of a TEXT segment."""
        body = 't1 JOIN "JOIN" ON t1.id = "JOIN".id'
        tokens = _tokenize_from_clause_body(body)
        self.assertEqual(sum(1 for k, _ in tokens if k == "JOINKW"), 1)
        self.assertEqual(sum(1 for k, _ in tokens if k == "CONDKW"), 1)
        text_values = [v for k, v in tokens if k == "TEXT"]
        self.assertTrue(any('"JOIN"' in t for t in text_values),
                        "The quoted identifier should appear in a TEXT token")

    def test_keyword_inside_brackets_ignored(self):
        """A bracket-quoted identifier containing a SQL keyword must not produce an
        extra CONDKW token; the bracketed string is captured as part of a TEXT segment."""
        body = "t1 JOIN [ON] ON t1.id = [ON].id"
        tokens = _tokenize_from_clause_body(body)
        self.assertEqual(sum(1 for k, _ in tokens if k == "JOINKW"), 1)
        self.assertEqual(sum(1 for k, _ in tokens if k == "CONDKW"), 1)
        text_values = [v for k, v in tokens if k == "TEXT"]
        self.assertTrue(any("[ON]" in t for t in text_values),
                        "The bracketed identifier should appear in a TEXT token")

    def test_keyword_inside_backticks_ignored(self):
        """A backtick-quoted identifier containing a SQL keyword must not produce an
        extra CONDKW token; the backtick string is captured as part of a TEXT segment."""
        body = "t1 JOIN `ON` ON t1.id = `ON`.id"
        tokens = _tokenize_from_clause_body(body)
        self.assertEqual(sum(1 for k, _ in tokens if k == "JOINKW"), 1)
        self.assertEqual(sum(1 for k, _ in tokens if k == "CONDKW"), 1)
        text_values = [v for k, v in tokens if k == "TEXT"]
        self.assertTrue(any("`ON`" in t for t in text_values),
                        "The backtick-quoted identifier should appear in a TEXT token")

    def test_using_keyword_tokenized_as_condkw(self):
        """USING is tokenized as a CONDKW, not ignored."""
        body = "t1 JOIN t2 USING (id)"
        tokens = _tokenize_from_clause_body(body)
        cond_values = [v for k, v in tokens if k == "CONDKW"]
        self.assertEqual(cond_values, ["USING"])


class TestClauseEndIndex(unittest.TestCase):
    def test_no_terminators(self):
        """Should return length of string if no terminators found."""
        sql = "SELECT * FROM my_table JOIN other_table ON a = b"
        self.assertEqual(clause_end_index(sql, 0), len(sql))

    def test_single_terminator(self):
        """Should return index of the terminator."""
        sql = "SELECT * FROM my_table WHERE a = 1"
        # 'WHERE' starts at index 25
        self.assertEqual(clause_end_index(sql, 0), sql.index("WHERE"))

        sql = "SELECT * FROM my_table GROUP BY a"
        self.assertEqual(clause_end_index(sql, 0), sql.index("GROUP BY"))

    def test_multiple_terminators(self):
        """Should return index of the first terminator found in the string."""
        sql = "SELECT * FROM my_table WHERE a = 1 GROUP BY a ORDER BY a"
        # Even though GROUP BY and ORDER BY exist, WHERE is first
        self.assertEqual(clause_end_index(sql, 0), sql.index("WHERE"))

        # If we start after WHERE, we should find GROUP BY
        start_after_where = sql.index("WHERE") + 5
        self.assertEqual(clause_end_index(sql, start_after_where), sql.index("GROUP BY"))

    def test_terminator_inside_subquery(self):
        """Should ignore terminators inside parentheses."""
        sql = "SELECT * FROM t1 JOIN (SELECT * FROM t2 WHERE b = 1) ON a = b WHERE a = 1"
        # The WHERE inside the subquery should be ignored.
        # We want the index of the last WHERE.
        self.assertEqual(clause_end_index(sql, 0), sql.rindex("WHERE"))

    def test_terminator_inside_quotes(self):
        """Should ignore terminators inside quotes or brackets."""
        sql = "SELECT * FROM t1 WHERE a = 'WHERE' GROUP BY b"
        # The 'WHERE' inside quotes should be ignored. We should find 'WHERE' keyword
        self.assertEqual(clause_end_index(sql, 0), sql.index("WHERE"))

        sql2 = "SELECT * FROM t1 JOIN [WHERE] u ON a = b GROUP BY b"
        # [WHERE] is a bracketed identifier; the parser enters mode='bracket' and ignores it
        self.assertEqual(clause_end_index(sql2, 0), sql2.index("GROUP BY"))

        sql3 = "SELECT * FROM t1 JOIN u ON a = `WHERE` GROUP BY b"
        self.assertEqual(clause_end_index(sql3, 0), sql3.index("GROUP BY"))

    def test_different_start_indices(self):
        """Should correctly offset the search based on start index."""
        sql = "SELECT * FROM my_table WHERE a = 1"
        self.assertEqual(clause_end_index(sql, 0), sql.index("WHERE"))

        # If start is past WHERE, it shouldn't find it
        self.assertEqual(clause_end_index(sql, sql.index("WHERE") + 1), len(sql))
class TestTokenize(unittest.TestCase):
    def test_tokenize_scenarios(self):
        """Test the tokenize function with various SQL inputs."""
        test_cases = [
            # description, sql_string, expected_tokens
            ("Basic SELECT query",
             "SELECT a, b FROM table1 WHERE id = 1",
             ['SELECT', 'a', ',', 'b', 'FROM', 'table1', 'WHERE', 'id', '=', '1']),

            # Note: E'...' parses as E, '...' while E"..." parses as E"..."
            ("Single, double, and E-quoted strings",
             "SELECT 'string', E'string2', \"col 1\", E\"esc\"",
             ['SELECT', "'string'", ',', 'E', "'string2'", ',', '"col 1"', ',', 'E"esc"']),

            # Note: 'it''s' is parsed as 'it', 's' by the regex currently.
            # This test ensures no unexpected regressions.
            ("Strings with escaped single quotes",
             "SELECT 'it''s'",
             ['SELECT', "'it'", "'s'"]),

            ("Bracketed and backticked identifiers",
             "SELECT [my table], `my col`",
             ['SELECT', '[my table]', ',', '`my col`']),

            ("Integer and float numbers",
             "SELECT 123, 45.67",
             ['SELECT', '123', ',', '45.67']),

            ("Multi-character operators",
             "SELECT a <= b, c >= d, e <> f, g != h, i := j, k -> l, m::n",
             ['SELECT', 'a', '<=', 'b', ',', 'c', '>=', 'd', ',',
              'e', '<>', 'f', ',', 'g', '!=', 'h', ',',
              'i', ':=', 'j', ',', 'k', '->', 'l', ',', 'm', '::', 'n']),

            ("Single-character operators and punctuation",
             "SELECT a + b - c * d / e % f",
             ['SELECT', 'a', '+', 'b', '-', 'c', '*', 'd', '/', 'e', '%', 'f']),

            ("Whitespace (spaces, tabs, newlines) should be ignored",
             "SELECT \n\ta  \r\n  b",
             ['SELECT', 'a', 'b'])
        ]

        for description, sql, expected in test_cases:
            with self.subTest(description=description):
                self.assertEqual(tokenize(sql), expected)


class TestClauseEndIndex(unittest.TestCase):
    def test_no_terminators(self):
        """Should return length of string if no terminators found."""
        sql = "SELECT * FROM my_table JOIN other_table ON a = b"
        self.assertEqual(clause_end_index(sql, 0), len(sql))

    def test_single_terminator(self):
        """Should return index of the first terminator."""
        test_cases = [
            ("with WHERE clause", "SELECT * FROM my_table WHERE a = 1", "WHERE"),
            ("with GROUP BY clause", "SELECT * FROM my_table GROUP BY a", "GROUP BY"),
        ]
        for description, sql, terminator in test_cases:
            with self.subTest(description=description):
                self.assertEqual(clause_end_index(sql, 0), sql.index(terminator))

    def test_multiple_terminators(self):
        """Should return index of the first terminator from start."""
        sql = "SELECT * FROM my_table WHERE a = 1 GROUP BY a ORDER BY a"
        self.assertEqual(clause_end_index(sql, 0), sql.index("WHERE"))

        start_after_where = sql.index("WHERE") + len("WHERE")
        self.assertEqual(clause_end_index(sql, start_after_where), sql.index("GROUP BY"))

    def test_terminator_inside_subquery(self):
        """Should ignore terminators inside nested parentheses."""
        sql = "SELECT * FROM t1 JOIN (SELECT * FROM t2 WHERE b = 1) ON a = b WHERE a = 1"
        self.assertEqual(clause_end_index(sql, 0), sql.rindex("WHERE"))

    def test_terminator_inside_quotes(self):
        """Should ignore terminators that appear inside quoted strings."""
        test_cases = [
            ("in single quotes", "SELECT * FROM t1 WHERE a = 'WHERE' GROUP BY b", "WHERE"),
            ("in brackets", "SELECT * FROM t1 JOIN u ON a = '[WHERE]' GROUP BY b", "GROUP BY"),
            ("in backticks", "SELECT * FROM t1 JOIN u ON a = `WHERE` GROUP BY b", "GROUP BY"),
        ]
        for description, sql, expected_terminator in test_cases:
            with self.subTest(description=description):
                self.assertEqual(clause_end_index(sql, 0), sql.index(expected_terminator))

    def test_different_start_indices(self):
        """Should honor starting position when searching for terminators."""
        sql = "SELECT * FROM my_table WHERE a = 1"
        self.assertEqual(clause_end_index(sql, 0), sql.index("WHERE"))
        self.assertEqual(clause_end_index(sql, sql.index("WHERE") + 1), len(sql))

class TestStripSqlComments(unittest.TestCase):
    def test_no_comments(self):
        sql = "SELECT * FROM my_table;"
        self.assertEqual(strip_sql_comments(sql), sql)

    def test_single_line_comment(self):
        sql = "SELECT * FROM my_table; -- this is a comment"
        expected = "SELECT * FROM my_table; "
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_single_line_comment_own_line(self):
        sql = "-- this is a comment\nSELECT * FROM my_table;"
        expected = "\nSELECT * FROM my_table;"
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_block_comment_single_line(self):
        sql = "SELECT /* comment */ * FROM my_table;"
        expected = "SELECT  * FROM my_table;"
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_block_comment_multi_line(self):
        sql = "SELECT /* multi\nline\ncomment */ * FROM my_table;"
        expected = "SELECT  * FROM my_table;"
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_multiple_comments(self):
        sql = "SELECT /* comment 1 */ * FROM my_table; -- comment 2"
        expected = "SELECT  * FROM my_table; "
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_empty_string(self):
        self.assertEqual(strip_sql_comments(""), "")

    def test_only_comment(self):
        self.assertEqual(strip_sql_comments("-- comment"), "")
        self.assertEqual(strip_sql_comments("/* comment */"), "")

    def test_no_newline_after_single_line_comment(self):
        sql = "SELECT * FROM my_table; -- comment without newline"
        expected = "SELECT * FROM my_table; "
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_empty_block_comment(self):
        sql = "SELECT /**/ * FROM my_table;"
        expected = "SELECT  * FROM my_table;"
        self.assertEqual(strip_sql_comments(sql), expected)

    def test_comment_like_sequences_in_strings(self):
        """Ensures comment-like sequences in string literals are not stripped."""
        with self.subTest("Line comment in string"):
            sql = "SELECT 'This is -- not a comment' FROM my_table;"
            self.assertEqual(strip_sql_comments(sql), sql)

        with self.subTest("Block comment in string"):
            sql = "SELECT 'This is /* not a comment */' FROM my_table;"
            self.assertEqual(strip_sql_comments(sql), sql)


class TestUppercaseOutsideQuotes(unittest.TestCase):
    def test_unquoted_text(self):
        self.assertEqual(uppercase_outside_quotes("select a from t"), "SELECT A FROM T")

    def test_single_quotes(self):
        self.assertEqual(uppercase_outside_quotes("select 'hello'"), "SELECT 'hello'")

    def test_double_quotes(self):
        self.assertEqual(uppercase_outside_quotes('select "myCol"'), 'SELECT "myCol"')

    def test_brackets(self):
        self.assertEqual(uppercase_outside_quotes("select [my Col]"), "SELECT [my Col]")

    def test_backticks(self):
        self.assertEqual(uppercase_outside_quotes("select `myCol`"), "SELECT `myCol`")

    def test_mixed_quotes(self):
        result = uppercase_outside_quotes("select 'a', \"b\", [c], `d` from t")
        self.assertEqual(result, "SELECT 'a', \"b\", [c], `d` FROM T")

    def test_escaped_single_quotes(self):
        result = uppercase_outside_quotes("select 'it''s'")
        self.assertEqual(result, "SELECT 'it''s'")

    def test_escaped_double_quotes(self):
        result = uppercase_outside_quotes('select "a""b"')
        self.assertEqual(result, 'SELECT "a""b"')

    def test_consecutive_quotes(self):
        result = uppercase_outside_quotes("select ''")
        self.assertEqual(result, "SELECT ''")

    def test_unclosed_quotes(self):
        # Should not crash on unclosed quotes
        result = uppercase_outside_quotes("select 'unclosed")
        self.assertIsInstance(result, str)

    def test_quotes_inside_quotes(self):
        result = uppercase_outside_quotes("""select 'he said "hi"' from t""")
        self.assertEqual(result, """SELECT 'he said "hi"' FROM T""")


class TestTopLevelFindKw(unittest.TestCase):
    def test_finds_top_level_keyword(self):
        """Should find a keyword at the top level."""
        sql = "SELECT a FROM t WHERE a = 1"
        self.assertEqual(top_level_find_kw(sql, "WHERE"), sql.index("WHERE"))

    def test_keyword_inside_single_quotes_ignored(self):
        """Keyword inside single-quoted string should not match."""
        sql = "SELECT 'WHERE' FROM t"
        self.assertEqual(top_level_find_kw(sql, "WHERE"), -1)

    def test_keyword_inside_double_quotes_ignored(self):
        """Keyword inside double-quoted identifier should not match."""
        sql = 'SELECT "WHERE" FROM t'
        self.assertEqual(top_level_find_kw(sql, "WHERE"), -1)

    def test_keyword_inside_brackets_ignored(self):
        """Keyword inside bracket-quoted identifier should not match."""
        sql = "SELECT [WHERE] FROM t"
        self.assertEqual(top_level_find_kw(sql, "WHERE"), -1)

    def test_keyword_inside_backticks_ignored(self):
        """Keyword inside backtick-quoted identifier should not match."""
        sql = "SELECT `WHERE` FROM t"
        self.assertEqual(top_level_find_kw(sql, "WHERE"), -1)

    def test_keyword_inside_subquery_ignored(self):
        """Keyword inside parenthesized subquery should not be treated as top-level."""
        sql = "SELECT * FROM (SELECT * FROM t WHERE id = 1) sub"
        self.assertEqual(top_level_find_kw(sql, "WHERE"), -1)

    def test_keyword_after_subquery_found(self):
        """Keyword after a subquery (at top level) should still be found."""
        sql = "SELECT * FROM (SELECT * FROM t WHERE id = 1) sub WHERE sub.x = 2"
        expected = sql.rindex("WHERE")
        self.assertEqual(top_level_find_kw(sql, "WHERE"), expected)

    def test_start_offset_skips_earlier_occurrence(self):
        """Using start offset should skip keyword occurrences before start."""
        sql = "SELECT a FROM t WHERE a = 1 ORDER BY a"
        where_idx = sql.index("WHERE")
        order_idx = sql.index("ORDER")
        # Starting after WHERE should not find WHERE again
        self.assertEqual(top_level_find_kw(sql, "WHERE", start=where_idx + 1), -1)
        # Should find ORDER BY from the beginning
        self.assertEqual(top_level_find_kw(sql, "ORDER", start=0), order_idx)

    def test_not_found_returns_minus_one(self):
        """Should return -1 when keyword is not present."""
        sql = "SELECT a FROM t"
        self.assertEqual(top_level_find_kw(sql, "WHERE"), -1)

    def test_case_insensitive(self):
        """Should match keyword regardless of case in SQL."""
        sql = "select a from t where a = 1"
        self.assertEqual(top_level_find_kw(sql, "WHERE"), sql.index("where"))

    def test_quoted_string_with_escaped_quote_then_keyword(self):
        """Escaped quotes inside string should not break parsing; keyword after string is found."""
        sql = "SELECT 'it''s fine' WHERE x = 1"
        self.assertEqual(top_level_find_kw(sql, "WHERE"), sql.index("WHERE"))


class TestSecurity(unittest.TestCase):
    def test_unbounded_stdin_dos(self):
        """Verify that read_from_stdin_two_parts limits read size to prevent DoS."""
        import sys
        from unittest.mock import patch
        from sql_compare import read_from_stdin_two_parts

        class MockStdin:
            def read(self, size=-1):
                if size == -1:
                    raise Exception("Unbounded read called!")
                return "a" * size

        with patch('sql_compare.MAX_FILE_SIZE_BYTES', 100), patch("sys.stdin", MockStdin()):
            with self.assertRaisesRegex(ValueError, "Input too large: stdin exceeds"):
                read_from_stdin_two_parts()

    def test_xss_in_html_report_summary(self):
        """Verify that XSS payloads in summary lines are escaped in HTML output."""
        import tempfile, os
        from sql_compare import generate_report
        xss_payload = '<script>alert("xss")</script>'
        result = {
            'ws_equal': True, 'exact_equal': False, 'canonical_equal': False,
            'summary': [xss_payload],
            'diff_ws': '', 'diff_norm': '', 'diff_can': '',
            'ws_a': '', 'ws_b': '', 'norm_a': 'SELECT 1', 'norm_b': 'SELECT 2',
            'can_a': 'SELECT 1', 'can_b': 'SELECT 2',
        }
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as f:
            tmp_path = f.name
        try:
            generate_report(result, 'both', 'html', tmp_path, False)
            with open(tmp_path, encoding='utf-8') as f:
                html_content = f.read()
            self.assertNotIn('<script>', html_content)
            self.assertIn('&lt;script&gt;', html_content)
        finally:
            os.unlink(tmp_path)



class TestTokenizeFromClauseBody(unittest.TestCase):
    def test_backticks(self):
        """Should correctly parse backticks in a FROM clause body."""
        from sql_compare import _tokenize_from_clause_body
        sql = "t1 JOIN t2 ON t1.`id` = t2.`id`"
        tokens = _tokenize_from_clause_body(sql)
        self.assertEqual(tokens, [
            ('TEXT', 't1'),
            ('JOINKW', 'JOIN'),
            ('TEXT', 't2'),
            ('CONDKW', 'ON'),
            ('TEXT', 't1.`id` = t2.`id`')
        ])
class TestCollapseWhitespace(unittest.TestCase):
    def test_collapse_whitespace_scenarios(self):
        """Test various scenarios for whitespace collapsing."""
        test_cases = {
            "basic_collapse": ("SELECT  *   FROM    t1", "SELECT * FROM t1"),
            "mixed_whitespace_sql": ("SELECT\t*\nFROM\r\nt1", "SELECT * FROM t1"),
            "mixed_whitespace_simple": ("A \t \n B", "A B"),
            "trimming_spaces": ("   SELECT * FROM t1  ", "SELECT * FROM t1"),
            "trimming_mixed": ("\n\tSELECT * FROM t1\r\n", "SELECT * FROM t1"),
            "no_whitespace_sql": ("SELECT*FROM(t1)", "SELECT*FROM(t1)"),
            "no_whitespace_word": ("word", "word"),
            "empty_string": ("", ""),
            "only_whitespace": ("   \t\n  ", ""),
        }

        for name, (input_str, expected) in test_cases.items():
            with self.subTest(name=name):
                self.assertEqual(collapse_whitespace(input_str), expected)


class TestRemoveOuterParentheses(unittest.TestCase):
    def test_basic_single_layer(self):
        """Should remove a single layer of outer parentheses."""
        sql = "(SELECT * FROM t)"
        self.assertEqual(remove_outer_parentheses(sql), "SELECT * FROM t")

    def test_multiple_layers(self):
        """Should remove multiple layers of outer parentheses."""
        sql = "(((SELECT * FROM t)))"
        self.assertEqual(remove_outer_parentheses(sql), "SELECT * FROM t")

    def test_no_parentheses(self):
        """Should return the string unmodified if no outer parentheses exist."""
        sql = "SELECT * FROM t"
        self.assertEqual(remove_outer_parentheses(sql), "SELECT * FROM t")

    def test_unmatched_parentheses(self):
        """Should return the string unmodified if parentheses are not matched at the ends."""
        sql = "(SELECT * FROM t"
        self.assertEqual(remove_outer_parentheses(sql), "(SELECT * FROM t")

        sql2 = "SELECT * FROM t)"
        self.assertEqual(remove_outer_parentheses(sql2), "SELECT * FROM t)")

    def test_not_full_statement(self):
        """Should not remove parentheses if they don't enclose the entire statement."""
        sql = "(SELECT a) UNION (SELECT b)"
        self.assertEqual(remove_outer_parentheses(sql), "(SELECT a) UNION (SELECT b)")

    def test_parentheses_inside_strings(self):
        """Should not be confused by parentheses inside quoted strings."""
        # The string starts with ( and ends with ), but the parentheses do not match each other structurally at the top level
        sql = "('()')"
        self.assertEqual(remove_outer_parentheses(sql), "'()'")

    def test_empty_string(self):
        """Should handle empty strings and whitespace correctly."""
        self.assertEqual(remove_outer_parentheses(""), "")
        self.assertEqual(remove_outer_parentheses("()"), "")
        self.assertEqual(remove_outer_parentheses(" ( ) "), "")

if __name__ == '__main__':
    unittest.main()
