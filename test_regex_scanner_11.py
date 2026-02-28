import re
from sql_compare import clause_end_index, top_level_find_kw

sql = "SELECT * FROM t where x = 2"
start_idx = sql.find("FROM") + 4

m = re.match(r"\bWHERE\b", "where x = 2")
print(bool(m))

m2 = re.match(r"\bWHERE\b", "where x = 2", flags=re.IGNORECASE)
print(bool(m2))
