import re
from sql_compare import top_level_find_kw

sql = "SELECT * FROM t where x = 2"
start_idx = sql.find("FROM") + 4

kw = "WHERE".upper()
i = start_idx
mode = None
level = 0
while i < len(sql):
    ch = sql[i]
    if mode is None:
        if ch == "'": mode = 'single'
        elif ch == '"': mode = 'double'
        elif ch == '[': mode = 'bracket'
        elif ch == '`': mode = 'backtick'
        elif ch == '(':
            level += 1
        elif ch == ')':
            level = max(0, level - 1)
        if level == 0:
            m = re.match(rf"\b{re.escape(kw)}\b", sql[i:])
            if m:
                print("matched at", i)
                break
    i += 1
