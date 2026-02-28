import unittest
from sql_compare import _parse_from_clause_body

class TestParseFromClauseBody(unittest.TestCase):
    def test_basic_inner_join(self):
        body = "t1 JOIN t2 ON t1.id = t2.id"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0], {
            "type": "INNER",
            "table": "t2",
            "cond_kw": "ON",
            "cond": "t1.id = t2.id"
        })

    def test_explicit_inner_join(self):
        body = "t1 INNER JOIN t2 ON t1.id = t2.id"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0], {
            "type": "INNER",
            "table": "t2",
            "cond_kw": "ON",
            "cond": "t1.id = t2.id"
        })

    def test_multiple_inner_joins(self):
        body = "t1 JOIN t2 ON t1.id = t2.id JOIN t3 ON t1.id = t3.id"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0], {
            "type": "INNER",
            "table": "t2",
            "cond_kw": "ON",
            "cond": "t1.id = t2.id"
        })
        self.assertEqual(segments[1], {
            "type": "INNER",
            "table": "t3",
            "cond_kw": "ON",
            "cond": "t1.id = t3.id"
        })




    def test_left_join(self):
        body = "t1 LEFT JOIN t2 ON t1.id = t2.id"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(segments[0], {
            "type": "LEFT",
            "table": "t2",
            "cond_kw": "ON",
            "cond": "t1.id = t2.id"
        })

    def test_left_outer_join(self):
        body = "t1 LEFT OUTER JOIN t2 ON t1.id = t2.id"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(segments[0], {
            "type": "LEFT",
            "table": "t2",
            "cond_kw": "ON",
            "cond": "t1.id = t2.id"
        })

    def test_right_join(self):
        body = "t1 RIGHT JOIN t2 ON t1.id = t2.id"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(segments[0], {
            "type": "RIGHT",
            "table": "t2",
            "cond_kw": "ON",
            "cond": "t1.id = t2.id"
        })

    def test_full_outer_join(self):
        body = "t1 FULL OUTER JOIN t2 ON t1.id = t2.id"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(segments[0], {
            "type": "FULL",
            "table": "t2",
            "cond_kw": "ON",
            "cond": "t1.id = t2.id"
        })

    def test_full_join(self):
        body = "t1 FULL JOIN t2 ON t1.id = t2.id"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(segments[0], {
            "type": "FULL",
            "table": "t2",
            "cond_kw": "ON",
            "cond": "t1.id = t2.id"
        })



    def test_cross_join(self):
        body = "t1 CROSS JOIN t2"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(segments[0], {
            "type": "CROSS",
            "table": "t2",
            "cond_kw": None,
            "cond": ""
        })

    def test_natural_join(self):
        body = "t1 NATURAL JOIN t2"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(segments[0], {
            "type": "NATURAL",
            "table": "t2",
            "cond_kw": None,
            "cond": ""
        })

    def test_natural_left_join(self):
        body = "t1 NATURAL LEFT JOIN t2"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(segments[0], {
            "type": "NATURAL LEFT",
            "table": "t2",
            "cond_kw": None,
            "cond": ""
        })




    def test_join_using(self):
        body = "t1 JOIN t2 USING (id)"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(segments[0], {
            "type": "INNER",
            "table": "t2",
            "cond_kw": "USING",
            "cond": "(id)"
        })




    def test_join_with_subquery_in_base(self):
        body = "(SELECT * FROM t1 WHERE id > 0) t JOIN t2 ON t.id = t2.id"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "(SELECT * FROM t1 WHERE id > 0) t")
        self.assertEqual(segments[0], {
            "type": "INNER",
            "table": "t2",
            "cond_kw": "ON",
            "cond": "t.id = t2.id"
        })

    def test_join_with_subquery_in_condition(self):
        body = "t1 JOIN t2 ON t1.id = (SELECT max(id) FROM t2)"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(segments[0], {
            "type": "INNER",
            "table": "t2",
            "cond_kw": "ON",
            "cond": "t1.id = (SELECT max(id) FROM t2)"
        })

    def test_join_with_parentheses(self):
        body = "(t1 JOIN t2 ON t1.id = t2.id) JOIN t3 ON t1.id = t3.id"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "(t1 JOIN t2 ON t1.id = t2.id)")
        self.assertEqual(segments[0], {
            "type": "INNER",
            "table": "t3",
            "cond_kw": "ON",
            "cond": "t1.id = t3.id"
        })




    def test_join_with_quotes(self):
        body = "t1 JOIN t2 ON t1.name = 'LEFT JOIN'"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0], {
            "type": "INNER",
            "table": "t2",
            "cond_kw": "ON",
            "cond": "t1.name = 'LEFT JOIN'"
        })

    def test_join_with_backticks(self):
        body = "`t1` JOIN `t2` ON `t1`.`id` = `t2`.`id`"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "`t1`")
        self.assertEqual(segments[0], {
            "type": "INNER",
            "table": "`t2`",
            "cond_kw": "ON",
            "cond": "`t1`.`id` = `t2`.`id`"
        })

    def test_join_with_double_quotes(self):
        body = 't1 JOIN t2 ON t1.name = "INNER JOIN"'
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(segments[0], {
            "type": "INNER",
            "table": "t2",
            "cond_kw": "ON",
            "cond": 't1.name = "INNER JOIN"'
        })

    def test_join_with_brackets(self):
        body = "[t1] JOIN [t2] ON [t1].[id] = [t2].[id]"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "[t1]")
        self.assertEqual(segments[0], {
            "type": "INNER",
            "table": "[t2]",
            "cond_kw": "ON",
            "cond": "[t1].[id] = [t2].[id]"
        })




    def test_complex_whitespace(self):
        body = "t1 \n  \t  INNER \n JOIN  \t t2 \n ON \n  t1.id \t  =   \n t2.id"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(segments[0], {
            "type": "INNER",
            "table": "t2",
            "cond_kw": "ON",
            "cond": "t1.id = t2.id"
        })

    def test_join_missing_on_or_using(self):
        # A malformed query or where ON/USING isn't correctly given but it should parse as much as possible
        body = "t1 JOIN t2"
        base, segments = _parse_from_clause_body(body)
        self.assertEqual(base, "t1")
        self.assertEqual(segments[0], {
            "type": "INNER",
            "table": "t2",
            "cond_kw": None,
            "cond": ""
        })

if __name__ == '__main__':
    unittest.main()
