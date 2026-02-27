import sql_compare
import unittest

class TestClauseEndIndex(unittest.TestCase):
    def test_clause_end_index(self):
        sql = "SELECT * FROM table WHERE id = 1 GROUP BY id HAVING count > 1 ORDER BY id LIMIT 10"

        # Test WHERE clause end
        # "WHERE" starts at index 20. clause_end_index should return start of "GROUP BY"
        start_where = sql.find("WHERE")
        expected_end_where = sql.find("GROUP BY")
        self.assertEqual(sql_compare.clause_end_index(sql, start_where + 5), expected_end_where)

        # Test GROUP BY clause end
        # "GROUP BY" starts at 33. clause_end_index should return start of "HAVING"
        start_group = sql.find("GROUP BY")
        expected_end_group = sql.find("HAVING")
        self.assertEqual(sql_compare.clause_end_index(sql, start_group + 8), expected_end_group)

        # Test HAVING clause end
        # "HAVING" starts at 45. clause_end_index should return start of "ORDER BY"
        start_having = sql.find("HAVING")
        expected_end_having = sql.find("ORDER BY")
        self.assertEqual(sql_compare.clause_end_index(sql, start_having + 6), expected_end_having)

        # Test ORDER BY clause end
        # "ORDER BY" starts at 60. clause_end_index should return start of "LIMIT"
        start_order = sql.find("ORDER BY")
        expected_end_order = sql.find("LIMIT")
        self.assertEqual(sql_compare.clause_end_index(sql, start_order + 8), expected_end_order)

        # Test LIMIT clause end (last clause)
        # "LIMIT" starts at 72. clause_end_index should return len(sql)
        start_limit = sql.find("LIMIT")
        expected_end_limit = len(sql)
        self.assertEqual(sql_compare.clause_end_index(sql, start_limit + 5), expected_end_limit)

    def test_no_keywords(self):
        sql = "SELECT * FROM table"
        start_from = sql.find("FROM")
        expected_end_from = len(sql)
        self.assertEqual(sql_compare.clause_end_index(sql, start_from + 4), expected_end_from)

    def test_keyword_in_string(self):
        # ensure keywords inside strings are ignored
        sql = "SELECT * FROM table WHERE name = 'GROUP BY'"
        start_where = sql.find("WHERE")
        expected_end_where = len(sql) # Should not find 'GROUP BY' inside the string
        self.assertEqual(sql_compare.clause_end_index(sql, start_where + 5), expected_end_where)

if __name__ == "__main__":
    unittest.main()
