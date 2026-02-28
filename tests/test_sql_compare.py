import unittest
from sql_compare import canonicalize_joins, uppercase_outside_quotes

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


class TestUppercaseOutsideQuotes(unittest.TestCase):
    def test_no_quotes(self):
        """Basic strings without any quotes should be completely uppercased."""
        self.assertEqual(uppercase_outside_quotes("select * from table"), "SELECT * FROM TABLE")
        self.assertEqual(uppercase_outside_quotes("where id = 1"), "WHERE ID = 1")
        self.assertEqual(uppercase_outside_quotes(""), "")

    def test_single_quotes(self):
        """Strings within single quotes should remain unchanged."""
        self.assertEqual(uppercase_outside_quotes("select 'abc' from t"), "SELECT 'abc' FROM T")
        self.assertEqual(uppercase_outside_quotes("where name = 'John Doe'"), "WHERE NAME = 'John Doe'")
        self.assertEqual(uppercase_outside_quotes("'all lowercase'"), "'all lowercase'")

    def test_double_quotes(self):
        """Strings within double quotes should remain unchanged."""
        self.assertEqual(uppercase_outside_quotes('select "col1" from t'), 'SELECT "col1" FROM T')
        self.assertEqual(uppercase_outside_quotes('where id = "user_id"'), 'WHERE ID = "user_id"')
        self.assertEqual(uppercase_outside_quotes('"all lowercase"'), '"all lowercase"')

    def test_brackets(self):
        """Strings within brackets should remain unchanged."""
        self.assertEqual(uppercase_outside_quotes('select [col 1] from t'), 'SELECT [col 1] FROM T')
        self.assertEqual(uppercase_outside_quotes('where id = [user id]'), 'WHERE ID = [user id]')

    def test_backticks(self):
        """Strings within backticks should remain unchanged."""
        self.assertEqual(uppercase_outside_quotes('select `col 1` from t'), 'SELECT `col 1` FROM T')
        self.assertEqual(uppercase_outside_quotes('where id = `user id`'), 'WHERE ID = `user id`')

    def test_multiple_quotes(self):
        """Combinations of different quotes should all be respected."""
        self.assertEqual(
            uppercase_outside_quotes('select `col 1`, [col 2] from t where name = \'John\' and "desc" = \'a"b\''),
            'SELECT `col 1`, [col 2] FROM T WHERE NAME = \'John\' AND "desc" = \'a"b\''
        )
        self.assertEqual(
            uppercase_outside_quotes('select \'a\' as "b", [c] as `d` from e'),
            'SELECT \'a\' AS "b", [c] AS `d` FROM E'
        )

    def test_escaped_single_quotes(self):
        """Escaped single quotes (double single quote) inside single quotes should be respected."""
        self.assertEqual(uppercase_outside_quotes("select 'O''Reilly' from t"), "SELECT 'O''Reilly' FROM T")
        self.assertEqual(uppercase_outside_quotes("where name = 'a''b''c'"), "WHERE NAME = 'a''b''c'")

    def test_escaped_double_quotes(self):
        """Escaped double quotes (double double quote) inside double quotes should be respected."""
        self.assertEqual(uppercase_outside_quotes('select "a""b" from t'), 'SELECT "a""b" FROM T')
        self.assertEqual(uppercase_outside_quotes('where id = "a""b"'), 'WHERE ID = "a""b"')

    def test_unclosed_quotes(self):
        """Unclosed quotes should not cause an error and should just run to the end of the string."""
        self.assertEqual(uppercase_outside_quotes("select 'abc"), "SELECT 'abc")
        self.assertEqual(uppercase_outside_quotes('select "abc'), 'SELECT "abc')
        self.assertEqual(uppercase_outside_quotes('select [abc'), 'SELECT [abc')
        self.assertEqual(uppercase_outside_quotes('select `abc'), 'SELECT `abc')

if __name__ == '__main__':
    unittest.main()
