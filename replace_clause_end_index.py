import re

with open('sql_compare.py', 'r') as f:
    content = f.read()

old_func = """def clause_end_index(sql: str, start: int) -> int:
    \"\"\"
    Find end index for a clause (FROM or WHERE) to the next top-level major keyword.
    \"\"\"
    terms = CLAUSE_TERMINATORS
    ends = []
    for term in SQL_CLAUSE_TERMINATORS:
        idx = top_level_find_kw(sql, term, start)
        if idx != -1: ends.append(idx)
    return min(ends) if ends else len(sql)"""

new_func = """def clause_end_index(sql: str, start: int) -> int:
    \"\"\"
    Find end index for a clause (FROM or WHERE) to the next top-level major keyword.
    \"\"\"
    level = 0
    for m in CLAUSE_SCANNER_RE.finditer(sql, start):
        token = m.group(0)
        ch = token[0]
        if ch == '(':
            level += 1
        elif ch == ')':
            level = max(0, level - 1)
        elif level == 0:
            if not (ch in ("'", '"', '[', '`') or token.upper().startswith("E\"")):
                return m.start()
    return len(sql)"""

if old_func in content:
    content = content.replace(old_func, new_func)
    with open('sql_compare.py', 'w') as f:
        f.write(content)
    print("Replaced clause_end_index")
else:
    print("Could not find exact old function signature")
