import unittest
from sql_compare import split_top_level

class TestSplitTopLevel(unittest.TestCase):
    def test_basic_split(self):
        self.assertEqual(split_top_level("a,b,c", ","), ["a", "b", "c"])
        self.assertEqual(split_top_level(" a , b , c ", ","), ["a", "b", "c"])

    def test_no_split(self):
        self.assertEqual(split_top_level("abc", ","), ["abc"])

    def test_quotes(self):
        # Single quotes
        self.assertEqual(split_top_level("a,'b,c',d", ","), ["a", "'b,c'", "d"])
        # Double quotes
        self.assertEqual(split_top_level('a,"b,c",d', ","), ["a", '"b,c"', "d"])
        # Mixed quotes
        self.assertEqual(split_top_level("a,'b,c',\"d,e\"", ","), ["a", "'b,c'", '"d,e"'])

    def test_parentheses(self):
        self.assertEqual(split_top_level("a,(b,c),d", ","), ["a", "(b,c)", "d"])
        self.assertEqual(split_top_level("(a,b),(c,d)", ","), ["(a,b)", "(c,d)"])

    def test_brackets_backticks(self):
        self.assertEqual(split_top_level("a,[b,c],d", ","), ["a", "[b,c]", "d"])
        self.assertEqual(split_top_level("a,`b,c`,d", ","), ["a", "`b,c`", "d"])

    def test_complex(self):
        self.assertEqual(split_top_level("a,(b,'c,d'),e", ","), ["a", "(b,'c,d')", "e"])
        self.assertEqual(split_top_level("select a, (select x,y from t) as sub from table", ","),
                         ["select a", "(select x,y from t) as sub from table"])

    def test_separators(self):
        self.assertEqual(split_top_level("a AND b AND c", " AND "), ["a", "b", "c"])
        self.assertEqual(split_top_level("a AND (b AND c) AND d", " AND "), ["a", "(b AND c)", "d"])

    def test_edge_cases(self):
        self.assertEqual(split_top_level("", ","), [])
        self.assertEqual(split_top_level(",", ","), [])
        self.assertEqual(split_top_level(",a,,b,", ","), ["a", "b"])

if __name__ == '__main__':
    unittest.main()
