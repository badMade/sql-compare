import re
from sql_compare import clause_end_index, top_level_find_kw

sql = "SELECT * FROM t where x = 2"
start_idx = sql.find("FROM") + 4

print("Original behavior check")
print("idx WHERE:", top_level_find_kw(sql, "WHERE", start_idx))
print("idx where:", top_level_find_kw(sql, "where", start_idx))

# The current code normalizes sql by making it uppercase outside of quotes before calling clause_end_index
# wait, let's check normalize_sql logic.
