import sql_compare
import sys

# Test behavior on substrings that look like keywords but aren't (e.g. part of identifier)
sql = "SELECT * FROM somewhere"
idx = sql_compare.clause_end_index(sql, 0)
print(f"Index for '{sql}': {idx} (Expected: {len(sql)})")

# Test real keyword
sql2 = "SELECT * FROM t WHERE x=1"
idx2 = sql_compare.clause_end_index(sql2, 0)
print(f"Index for '{sql2}': {idx2} (Expected to point to WHERE)")
