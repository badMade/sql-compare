from sql_compare import clause_end_index, top_level_find_kw

sql = "SELECT * FROM t where x = 2"
start_idx = sql.find("FROM") + 4

# Oh wait! top_level_find_kw matched \bWHERE\b using re.match(..., sql[i:]), which is CASE-SENSITIVE by default because there are no flags!
import re
print(re.match(r"\bWHERE\b", "WHERE x = 2"))
print(re.match(r"\bWHERE\b", "where x = 2"))
