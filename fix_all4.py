import re

with open("sql_compare.py", "r", encoding="utf-8") as f:
    content = f.read()

# Instead of re.match, I will use `re.match` exactly the way it works on `sql[i:]` using literal string replacement so backslash `b` won't be mangled.
new_top_level = """def top_level_find_kw(sql: str, kw: str, start: int = 0):
    \"\"\"Find top-level occurrence of keyword kw (word boundary) starting at start.\"\"\"
    kw = kw.upper()
    i = start
    scanner = _SQLScanner()
    while i < len(sql):
        ch = sql[i]
        next_ch = sql[i + 1] if i + 1 < len(sql) else None

        if scanner.level == 0 and scanner.mode is None:
            # We explicitly replace `\\b` in the string so that python uses raw backslash.
            m = re.match(r"\\b" + re.escape(kw) + r"\\b", sql[i:], flags=re.IGNORECASE)
            if m: return i

        skip = scanner.update(ch, next_ch)
        i += skip + 1
    return -1"""

# Actually, the string literal `r"\b"` inside `new_top_level` evaluates to `\b` inside python.
# Oh! Wait! In python string literals:
# `r"\b"` evaluates to string of length 2: backslash, then b.
# Wait, I did `m = re.match(r"\\b" ...)` in `fix_all3.py`
# This means the code inside `sql_compare.py` became `m = re.match(r"\b" ...)`
# Let me check `sql_compare.py` now.
