with open("tests/test_sql_compare.py", "r") as f:
    content = f.read()

# Replace test_ignore_inside_quotes
old_quotes = """    def test_ignore_inside_quotes(self):
        self.assertEqual(split_top_level("'A, B', C", ","), ["'A, B'", "C"])
        self.assertEqual(split_top_level('"A, B", C', ","), ['"A, B"', "C"])
        self.assertEqual(split_top_level("A = 'test AND case' AND B = 1", " AND "), ["A = 'test AND case'", "B = 1"])"""
new_quotes = """    def test_ignore_inside_quotes(self):
        test_cases = [
            ("single quotes", "'A, B', C", ",", ["'A, B'", "C"]),
            ("double quotes", '"A, B", C', ",", ['"A, B"', "C"]),
            ("separator in string", "A = 'test AND case' AND B = 1", " AND ", ["A = 'test AND case'", "B = 1"]),
        ]
        for description, sql, sep, expected in test_cases:
            with self.subTest(description=description):
                self.assertEqual(split_top_level(sql, sep), expected)"""

content = content.replace(old_quotes, new_quotes)

# Replace test_ignore_inside_brackets_backticks
old_brackets = """    def test_ignore_inside_brackets_backticks(self):
        self.assertEqual(split_top_level("[A, B], C", ","), ["[A, B]", "C"])
        self.assertEqual(split_top_level("`A, B`, C", ","), ["`A, B`", "C"])"""
new_brackets = """    def test_ignore_inside_brackets_backticks(self):
        test_cases = [
            ("brackets", "[A, B], C", ",", ["[A, B]", "C"]),
            ("backticks", "`A, B`, C", ",", ["`A, B`", "C"]),
        ]
        for description, sql, sep, expected in test_cases:
            with self.subTest(description=description):
                self.assertEqual(split_top_level(sql, sep), expected)"""

content = content.replace(old_brackets, new_brackets)

# Replace test_ignore_inside_parentheses
old_parens = """    def test_ignore_inside_parentheses(self):
        self.assertEqual(split_top_level("A(1, 2), B", ","), ["A(1, 2)", "B"])
        self.assertEqual(split_top_level("(A AND B) AND C", " AND "), ["(A AND B)", "C"])"""
new_parens = """    def test_ignore_inside_parentheses(self):
        test_cases = [
            ("function call", "A(1, 2), B", ",", ["A(1, 2)", "B"]),
            ("grouped expression", "(A AND B) AND C", " AND ", ["(A AND B)", "C"]),
        ]
        for description, sql, sep, expected in test_cases:
            with self.subTest(description=description):
                self.assertEqual(split_top_level(sql, sep), expected)"""

content = content.replace(old_parens, new_parens)

with open("tests/test_sql_compare.py", "w") as f:
    f.write(content)
