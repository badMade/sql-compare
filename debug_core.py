from sql_compare.core import normalize_sql, collapse_whitespace_smart

s = "SELECT '  keep spaces  ' FROM t"
print(f"Original: '{s}'")
c1 = collapse_whitespace_smart(s)
print(f"Collapsed 1: '{c1}'")

from sql_compare.core import uppercase_outside_quotes
u = uppercase_outside_quotes(c1)
print(f"Uppercased: '{u}'")

c2 = collapse_whitespace_smart(u)
print(f"Collapsed 2: '{c2}'")

print(f"Final: '{normalize_sql(s)}'")
