from sql_compare import _parse_from_clause_body

sql = "FROM t1 JOIN t3 ON t1.id=t3.id JOIN t2 ON t1.id=t2.id"
print(_parse_from_clause_body(sql))
