from sql_compare import clause_end_index, top_level_find_kw

sql = "SELECT * FROM t where x = 2"
start_idx = sql.find("FROM") + 4
print("Original using top_level_find_kw:")
print("WHERE:", top_level_find_kw(sql, "WHERE", start_idx))

# The actual original clause_end_index does this:
ends = []
for term in ["WHERE"]:
    idx = top_level_find_kw(sql, term, start_idx)
    if idx != -1: ends.append(idx)
print("ends:", ends)
