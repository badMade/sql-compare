import re
from sql_compare import clause_end_index, top_level_find_kw

test_cases = [
    ("SELECT * FROM t WHERE a=1", 16),
    ("SELECT * FROM t GROUP BY a", 16),
    ("SELECT * FROM t WHERE a='GROUP BY'", 16),
    ("SELECT * FROM t WHERE a=(SELECT MAX(id) FROM b WHERE id > 1) GROUP BY a", 16),
    ("SELECT * FROM [t GROUP BY x] GROUP BY a", 29),
    ("SELECT * FROM t", 15),
    ("SELECT * FROM t where x = 2", 27), # because "where" is not "WHERE"
    ("SELECT * FROM t e\"WHERE\" WHERE x = 2", 25),
    ("SELECT * FROM t E\"WHERE\" WHERE x = 2", 25),
    ("SELECT * FROM t E\"WHERE \" WHERE x = 2", 26),
]

for sql, expected in test_cases:
    start_idx = sql.find("FROM") + 4
    if start_idx == 3:
        start_idx = 0
    idx = clause_end_index(sql, start_idx)
    if idx != expected:
        print(f"MISMATCH! SQL: {sql} => {idx} != {expected}")
    else:
        print(f"MATCH! SQL: {sql} => {idx}")
