from sql_compare import clause_end_index

sql = "SELECT * FROM my_table SOWHERE id=1"
print(clause_end_index(sql, 15))
