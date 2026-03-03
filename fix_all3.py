import re

with open("sql_compare.py", "r", encoding="utf-8") as f:
    content = f.read()

# OK, the python strings `r"\b"` or string literal `"\b"` is causing chaos.
# I am going to write EXACTLY `re.match(r"\b" + re.escape(kw) + r"\b", sql[i:], flags=re.IGNORECASE)` to the file using literal string replacement.
new_top_level = """def top_level_find_kw(sql: str, kw: str, start: int = 0):
    \"\"\"Find top-level occurrence of keyword kw (word boundary) starting at start.\"\"\"
    kw = kw.upper()
    i = start
    scanner = _SQLScanner()
    while i < len(sql):
        ch = sql[i]
        next_ch = sql[i + 1] if i + 1 < len(sql) else None

        if scanner.level == 0 and scanner.mode is None:
            m = re.match(r"\\b" + re.escape(kw) + r"\\b", sql[i:], flags=re.IGNORECASE)
            if m: return i

        skip = scanner.update(ch, next_ch)
        i += skip + 1
    return -1"""

old_top_level_pattern = re.compile(r'def top_level_find_kw\(sql: str, kw: str, start: int = 0\):.*?(?=\n\n\ndef clause_end_index)', re.DOTALL)
content = old_top_level_pattern.sub(new_top_level, content)

with open("sql_compare.py", "w", encoding="utf-8") as f:
    f.write(content)
