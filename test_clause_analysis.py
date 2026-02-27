import unittest
from sql_compare import clause_end_index

class TestClauseEndIndex(unittest.TestCase):
    def test_basic(self):
        sql = "SELECT * FROM t WHERE a=1 ORDER BY b"
        # Search starting after "WHERE " (index 21)
        # "SELECT * FROM t WHERE " is 22 chars long
        # "SELECT * FROM t WHERE" is 21 chars long
        # valid start index for clause_end_index is typically right after the keyword

        # let's find indices manually to be sure
        where_idx = sql.find("WHERE")
        start = where_idx + 5
        end = clause_end_index(sql, start)
        self.assertEqual(sql[end:], "ORDER BY b")

    def test_quoted_keywords(self):
        sql = "SELECT * FROM t WHERE a='ORDER BY' GROUP BY x"
        where_idx = sql.find("WHERE")
        start = where_idx + 5
        end = clause_end_index(sql, start)
        self.assertEqual(sql[end:], "GROUP BY x")

    def test_nested_parens(self):
        sql = "SELECT * FROM t WHERE a=(SELECT 1 UNION SELECT 2) LIMIT 1"
        where_idx = sql.find("WHERE")
        start = where_idx + 5
        end = clause_end_index(sql, start)
        self.assertEqual(sql[end:], "LIMIT 1")

    def test_backticks(self):
        sql = "SELECT * FROM t WHERE a=`ORDER BY`"
        where_idx = sql.find("WHERE")
        start = where_idx + 5
        end = clause_end_index(sql, start)
        self.assertEqual(end, len(sql))

    def test_brackets(self):
        sql = "SELECT * FROM t WHERE a=[GROUP BY]"
        where_idx = sql.find("WHERE")
        start = where_idx + 5
        end = clause_end_index(sql, start)
        self.assertEqual(end, len(sql))

    def test_no_keywords(self):
        sql = "SELECT * FROM t WHERE a=1"
        where_idx = sql.find("WHERE")
        start = where_idx + 5
        end = clause_end_index(sql, start)
        self.assertEqual(end, len(sql))

    def test_case_insensitivity(self):
        sql = "SELECT * FROM t WHERE a=1 ORDER BY B"
        where_idx = sql.find("WHERE")
        start = where_idx + 5
        end = clause_end_index(sql, start)
        self.assertEqual(sql[end:].upper(), "ORDER BY B")

if __name__ == "__main__":
    unittest.main()
