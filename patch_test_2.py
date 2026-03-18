with open("tests/test_sql_compare.py", "r") as f:
    content = f.read()

old_consec = """    def test_consecutive_separators(self):
        self.assertEqual(split_top_level("A,,B", ","), ["A", "B"])
        self.assertEqual(split_top_level("A AND  AND B", " AND "), ["A", "B"])"""

new_consec = """    def test_consecutive_separators(self):
        test_cases = [
            ("consecutive commas", "A,,B", ",", ["A", "B"]),
            ("consecutive word separators", "A AND  AND B", " AND ", ["A", "B"]),
        ]
        for description, sql, sep, expected in test_cases:
            with self.subTest(description=description):
                self.assertEqual(split_top_level(sql, sep), expected)"""

content = content.replace(old_consec, new_consec)

with open("tests/test_sql_compare.py", "w") as f:
    f.write(content)
