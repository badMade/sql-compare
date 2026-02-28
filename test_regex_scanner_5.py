from sql_compare import clause_end_index, top_level_find_kw

sql = "SELECT * FROM t where x = 2"
start_idx = sql.find("FROM") + 4
print(clause_end_index(sql, start_idx))
print("idx:", top_level_find_kw(sql, "WHERE", start_idx))
