import unittest
from sql_compare import _parse_from_clause_body
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



class TestParseFromClauseBody(unittest.TestCase):
    def test_basic_join(self):
        """Test parsing of a simple JOIN with ON condition."""
        sql = "t1 JOIN t2 ON t1.id = t2.id"
        base, segments = _parse_from_clause_body(sql)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0], {"type": "INNER", "table": "t2", "cond_kw": "ON", "cond": "t1.id = t2.id"})

    def test_mixed_join_types(self):
        """Test parsing of various join types (LEFT, RIGHT, FULL OUTER, CROSS, NATURAL)."""
        sql = "t1 LEFT JOIN t2 ON x RIGHT JOIN t3 ON y FULL OUTER JOIN t4 ON z CROSS JOIN t5 NATURAL JOIN t6"
        base, segments = _parse_from_clause_body(sql)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 5)
        self.assertEqual(segments[0], {"type": "LEFT", "table": "t2", "cond_kw": "ON", "cond": "x"})
        self.assertEqual(segments[1], {"type": "RIGHT", "table": "t3", "cond_kw": "ON", "cond": "y"})
        self.assertEqual(segments[2], {"type": "FULL", "table": "t4", "cond_kw": "ON", "cond": "z"})
        self.assertEqual(segments[3], {"type": "CROSS", "table": "t5", "cond_kw": None, "cond": ""})
        self.assertEqual(segments[4], {"type": "NATURAL", "table": "t6", "cond_kw": None, "cond": ""})

    def test_condition_types(self):
        """Test ON vs USING conditions."""
        sql = "t1 JOIN t2 USING (id, name) JOIN t3 ON t1.id = t3.id"
        base, segments = _parse_from_clause_body(sql)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0], {"type": "INNER", "table": "t2", "cond_kw": "USING", "cond": "(id, name)"})
        self.assertEqual(segments[1], {"type": "INNER", "table": "t3", "cond_kw": "ON", "cond": "t1.id = t3.id"})

    def test_quoted_identifiers(self):
        """Test that join keywords inside quoted identifiers are ignored."""
        sql = "t1 JOIN \"LEFT JOIN\" ON t1.id = \"LEFT JOIN\".id JOIN [CROSS JOIN] ON t1.id = [CROSS JOIN].id JOIN `NATURAL JOIN` ON t1.id = `NATURAL JOIN`.id JOIN 'INNER JOIN' ON t1.id = 'INNER JOIN'.id"
        base, segments = _parse_from_clause_body(sql)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 4)
        self.assertEqual(segments[0], {"type": "INNER", "table": "\"LEFT JOIN\"", "cond_kw": "ON", "cond": "t1.id = \"LEFT JOIN\".id"})
        self.assertEqual(segments[1], {"type": "INNER", "table": "[CROSS JOIN]", "cond_kw": "ON", "cond": "t1.id = [CROSS JOIN].id"})
        self.assertEqual(segments[2], {"type": "INNER", "table": "`NATURAL JOIN`", "cond_kw": "ON", "cond": "t1.id = `NATURAL JOIN`.id"})
        self.assertEqual(segments[3], {"type": "INNER", "table": "'INNER JOIN'", "cond_kw": "ON", "cond": "t1.id = 'INNER JOIN'.id"})

    def test_subqueries(self):
        """Test that join keywords inside parenthesized subqueries are ignored."""
        sql = "t1 JOIN (SELECT * FROM t2 LEFT JOIN t3 ON x) AS sub ON t1.id = sub.id"
        base, segments = _parse_from_clause_body(sql)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0], {"type": "INNER", "table": "(SELECT * FROM t2 LEFT JOIN t3 ON x) AS sub", "cond_kw": "ON", "cond": "t1.id = sub.id"})

    def test_whitespace_and_newlines(self):
        """Test parsing with multiple spaces, tabs, and newlines."""
        sql = "t1   \n\t  JOIN \n t2 \n  ON \n\t  t1.id \n = \n t2.id"
        base, segments = _parse_from_clause_body(sql)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0], {"type": "INNER", "table": "t2", "cond_kw": "ON", "cond": "t1.id = t2.id"})

    def test_multiple_outer_joins(self):
        """Test FULL OUTER JOIN variations."""
        sql = "t1 FULL OUTER JOIN t2 ON a = b LEFT OUTER JOIN t3 ON c = d RIGHT OUTER JOIN t4 ON e = f"
        base, segments = _parse_from_clause_body(sql)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 3)
        self.assertEqual(segments[0], {"type": "FULL", "table": "t2", "cond_kw": "ON", "cond": "a = b"})
        self.assertEqual(segments[1], {"type": "LEFT", "table": "t3", "cond_kw": "ON", "cond": "c = d"})
        self.assertEqual(segments[2], {"type": "RIGHT", "table": "t4", "cond_kw": "ON", "cond": "e = f"})


if __name__ == '__main__':
    unittest.main()
