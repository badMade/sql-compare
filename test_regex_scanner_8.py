from sql_compare import top_level_find_kw

sql = "SELECT * FROM t WHERE x = 2"
start_idx = sql.find("FROM") + 4
print("idx WHERE:", top_level_find_kw(sql, "WHERE", start_idx))
