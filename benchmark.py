import time
import timeit
from sql_compare import clause_end_index, top_level_find_kw

sql = """
SELECT a, b, c
FROM my_table
WHERE id = 1
  AND name = 'John Doe'
  AND (status = 'active' OR status = 'pending')
  AND created_at > '2020-01-01'
GROUP BY a, b, c
ORDER BY a
LIMIT 10
""" * 1000  # Make it long

print("Length of sql:", len(sql))
start_idx = sql.find("FROM")

def bench():
    clause_end_index(sql, start_idx + 4)

print(timeit.timeit(bench, number=10))
