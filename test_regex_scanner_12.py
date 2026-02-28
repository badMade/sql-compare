import re
from sql_compare import clause_end_index, uppercase_outside_quotes

# Wait, `uppercase_outside_quotes` is called BEFORE any parsing in canonicalization.
sql1 = "SELECT * FROM t where x = 2"
sql2 = uppercase_outside_quotes(sql1)
print(f"sql1: {sql1}")
print(f"sql2: {sql2}")

# So if we are matching against sql2, "WHERE" is uppercase!
start_idx = sql2.find("FROM") + 4
print("Original on sql2:", clause_end_index(sql2, start_idx))
