import unittest
from sql_compare import canonicalize_joins, clause_end_index, tokenize, top_level_find_kw

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

class TestTopLevelFindKw(unittest.TestCase):
    def test_keyword_in_single_quotes_not_matched(self):
        """Keyword inside single-quoted string should not be returned."""
        sql = "SELECT * FROM t1 WHERE a = 'WHERE x = 1'"
        # The real top-level WHERE is at the first occurrence; the one inside quotes is skipped.
        idx = top_level_find_kw(sql, "WHERE", 0)
        self.assertEqual(idx, sql.index("WHERE"))
        # There is only one top-level WHERE; searching past it yields -1.
        self.assertEqual(top_level_find_kw(sql, "WHERE", idx + 1), -1)

    def test_keyword_in_double_quotes_not_matched(self):
        """Keyword inside double-quoted identifier should not be returned."""
        sql = 'SELECT "FROM other" FROM t1'
        # The FROM inside double quotes must be skipped; only the top-level FROM counts.
        idx = top_level_find_kw(sql, "FROM", 0)
        self.assertEqual(sql[idx:idx + 4], "FROM")
        # Confirm it is the second FROM (after the quoted one).
        self.assertGreater(idx, sql.index('"FROM other"'))

    def test_keyword_in_brackets_not_matched(self):
        """Keyword inside a bracketed identifier should not be returned."""
        sql = "SELECT [WHERE col] FROM t1 WHERE id = 1"
        idx = top_level_find_kw(sql, "WHERE", 0)
        # Should find the real WHERE, not the one inside [WHERE col].
        self.assertEqual(sql[idx:idx + 5], "WHERE")
        self.assertGreater(idx, sql.index("[WHERE col]"))

    def test_keyword_in_backticks_not_matched(self):
        """Keyword inside a backtick-quoted identifier should not be returned."""
        sql = "SELECT `FROM_alias` FROM t1"
        idx = top_level_find_kw(sql, "FROM", 0)
        # The backtick-enclosed token `FROM_alias` does not contain a word-boundary FROM,
        # but the real FROM keyword should be found at the top level.
        self.assertEqual(sql[idx:idx + 4], "FROM")
        self.assertGreater(idx, sql.index("`FROM_alias`"))

    def test_keyword_in_subquery_not_matched(self):
        """Keyword inside a parenthesized subquery should not be returned."""
        sql = "SELECT * FROM (SELECT * FROM inner_t WHERE b = 1) sub WHERE a = 1"
        idx = top_level_find_kw(sql, "WHERE", 0)
        # Should return the outermost WHERE, not the one inside the subquery.
        self.assertEqual(sql[idx:idx + 5], "WHERE")
        self.assertEqual(idx, sql.rindex("WHERE"))

    def test_start_offset_skips_earlier_occurrences(self):
        """Passing a start offset should skip keywords before that position."""
        sql = "SELECT a FROM t1 WHERE a = 1 GROUP BY a ORDER BY a"
        where_i = top_level_find_kw(sql, "WHERE", 0)
        self.assertGreaterEqual(where_i, 0)
        # Starting past WHERE should not find WHERE again.
        self.assertEqual(top_level_find_kw(sql, "WHERE", where_i + 1), -1)

    def test_keyword_not_present_returns_minus_one(self):
        """Should return -1 when the keyword is not present at all."""
        sql = "SELECT a FROM t1"
        self.assertEqual(top_level_find_kw(sql, "WHERE", 0), -1)

    def test_multiword_keyword_in_subquery_not_matched(self):
        """Multi-word keyword inside a subquery should not be returned at top level."""
        sql = "SELECT * FROM (SELECT a FROM t2 GROUP BY a) sub GROUP BY b"
        idx = top_level_find_kw(sql, "GROUP BY", 0)
        # Should find the outermost GROUP BY, not the one inside the subquery.
        self.assertEqual(idx, sql.rindex("GROUP BY"))


if __name__ == '__main__':
    unittest.main()
